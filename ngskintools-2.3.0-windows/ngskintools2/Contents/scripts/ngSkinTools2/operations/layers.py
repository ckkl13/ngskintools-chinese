# -*- coding: UTF-8 -*-
import random

from maya import cmds

import ngSkinTools2.api
from ngSkinTools2 import signal
from ngSkinTools2.api import Mirror
from ngSkinTools2.api.layers import generate_layer_name
from ngSkinTools2.api.log import getLogger
from ngSkinTools2.api.pyside import QAction, QtCore
from ngSkinTools2.api.session import session, withSession
from ngSkinTools2.decorators import undoable
from ngSkinTools2.ui import dialogs, qt
from ngSkinTools2.ui.action import Action
from ngSkinTools2.ui.options import config

logger = getLogger("layer operations")


@withSession
@undoable
def initializeLayers(createFirstLayer=True):
    if session.state.layersAvailable:
        return  # ignore

    target = session.state.selectedSkinCluster

    layers = ngSkinTools2.api.init_layers(target)
    with ngSkinTools2.api.suspend_updates(target):
        if createFirstLayer:
            layer = layers.add(u"基础权重")
            layer.set_current()
        Mirror(target).set_mirror_config(config.mirrorInfluencesDefaults)

    session.events.targetChanged.emitIfChanged()

    if ngSkinTools2.api.is_slow_mode_skin_cluster(target):
        dialogs.info(
            "ngSkinTools切换到慢maya API设置皮肤集群权重为这个skinCluster，以解决玛雅bug时skinCluster使用dg节点作为输入."
        )


@undoable
def addLayer():
    layers = ngSkinTools2.api.Layers(session.state.selectedSkinCluster)

    def guessParent():
        currentLayer = layers.current_layer()
        if currentLayer is None:
            return None

        # current layer is a parent?
        if currentLayer.num_children > 0:
            return currentLayer

        return currentLayer.parent

    with ngSkinTools2.api.suspend_updates(layers.mesh):
        new_layer = layers.add(generate_layer_name(session.state.all_layers, u"新图层"))
        new_layer.parent = guessParent()

        session.events.layerListChanged.emitIfChanged()
        setCurrentLayer(new_layer)

    return new_layer


def build_action_initialize_layers(session, parent):
    from ngSkinTools2.ui import actions

    from . import import_v1_actions

    def do_initialize():
        if import_v1_actions.can_import(session):
            q = (
                "这个网格上有以前版本的ngSkinTools的皮肤层,这个操作将初始化."
                "从头开始蒙皮层，丢弃之前的层信息。你想继续吗?"
            )
            if not dialogs.yesNo(q):
                return

        initializeLayers()

    result = actions.define_action(parent, "初始化蒙皮图层", callback=do_initialize)

    @signal.on(session.events.nodeSelectionChanged)
    def update():
        result.setEnabled(session.state.selectedSkinCluster is not None)

    update()

    return result


def buildAction_createLayer(session, parent):
    from ngSkinTools2.ui import actions

    result = actions.define_action(parent, "创建图层", callback=addLayer, icon=":/newLayerEmpty.png", shortcut=QtCore.Qt.Key_Insert)

    @signal.on(session.events.targetChanged)
    def update_to_target():
        result.setEnabled(session.state.layersAvailable)

    update_to_target()

    return result


def buildAction_deleteLayer(session, parent):
    from ngSkinTools2.ui import actions

    result = actions.define_action(parent, "删除图层", callback=deleteSelectedLayers, shortcut=QtCore.Qt.Key_Delete)

    @signal.on(session.context.selected_layers.changed, session.events.targetChanged, qtParent=parent)
    def update_to_target():
        result.setEnabled(session.state.layersAvailable and bool(session.context.selected_layers(default=[])))

    update_to_target()

    return result


@undoable
def setCurrentLayer(layer):
    """
    :type layer: ngSkinTools2.api.layers.Layer
    """
    if not session.active():
        logger.info("未设置当前图层:没有会话")

    if not session.state.layersAvailable:
        logger.info("未设置当前图层:未启用图层")

    logger.info("设置当前图层为 %r 上的 %r", layer, session.state.selectedSkinCluster)
    layer.set_current()
    session.events.currentLayerChanged.emitIfChanged()


def getCurrentLayer():
    layers = ngSkinTools2.api.Layers(session.state.selectedSkinCluster)
    return layers.current_layer()


@undoable
def renameLayer(layer, newName):
    layer.name = newName
    cmds.evalDeferred(session.events.layerListChanged.emitIfChanged)


@undoable
def deleteSelectedLayers():
    layers = ngSkinTools2.api.Layers(session.state.selectedSkinCluster)
    for i in session.context.selected_layers(default=[]):
        layers.delete(i)

    session.events.layerListChanged.emitIfChanged()
    session.events.currentLayerChanged.emitIfChanged()


class ToggleEnabledAction(Action):
    name = "启用选中图层"
    checkable = True

    def __init__(self, session):
        Action.__init__(self, session)

    def checked(self):
        """
        return true if most of selected layers are enabled
        :return:
        """
        layers = session.context.selected_layers(default=[])
        if not layers:
            return True

        enabled_disabled_balance = 0
        for layer in layers:
            try:
                # eat up the exception if layer id is invalid
                enabled_disabled_balance += 1 if layer.enabled else -1
            except:
                pass

        return enabled_disabled_balance >= 0

    def run(self):
        enabled = not self.checked()
        selected_layers = session.context.selected_layers()
        if not selected_layers:
            return

        for i in selected_layers:
            i.enabled = enabled

        logger.info("图层切换: %r", selected_layers)

        session.events.layerListChanged.emitIfChanged()

    def enabled(self):
        return session.state.layersAvailable and bool(session.context.selected_layers(default=[]))

    def update_on_signals(self):
        return [session.context.selected_layers.changed, session.events.layerListChanged, session.events.targetChanged]


def build_action_randomize_influences_colors(session, parent):
    """
    builds a UI action for randomly choosing new colors for influences
    :type session: ngSkinTools2.api.session.Session
    """

    result = QAction("随机颜色", parent)
    result.setToolTip("为每个影响物选择随机颜色，从Maya的索引颜色调色板中选择")

    def color_filter(c):
        brightness = c[0] * c[0] + c[1] * c[1] + c[2] * c[2]
        return brightness > 0.001 and brightness < 0.99  # just a fancy way to skip white and black

    colors = set([tuple(cmds.colorIndex(i, q=True)) for i in range(1, 30)])
    colors = [c for c in colors if color_filter(c)]

    @qt.on(result.triggered)
    def triggered():
        if session.state.selectedSkinCluster is None:
            return
        layers = ngSkinTools2.api.Layers(session.state.selectedSkinCluster)
        layers.config.influence_colors = {i.logicalIndex: random.choice(colors) for i in layers.list_influences()}

    return result
