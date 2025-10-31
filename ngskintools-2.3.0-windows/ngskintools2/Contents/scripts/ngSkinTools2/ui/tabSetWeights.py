# -*- coding: UTF-8 -*-
from ngSkinTools2 import signal
from ngSkinTools2.api import PaintMode, PaintModeSettings, flood_weights
from ngSkinTools2.api.log import getLogger
from ngSkinTools2.api.pyside import QAction, QActionGroup, QtWidgets
from ngSkinTools2.api.python_compatibility import Object
from ngSkinTools2.api.session import session
from ngSkinTools2.signal import Signal
from ngSkinTools2.ui import qt, widgets
from ngSkinTools2.ui.layout import TabSetup, createTitledRow
from ngSkinTools2.ui.ui_lock import UiLock

log = getLogger("tab set weights")


def make_presets():
    presets = {m: PaintModeSettings() for m in PaintMode.all()}
    for k, v in presets.items():
        v.mode = k

    presets[PaintMode.smooth].intensity = 0.3
    presets[PaintMode.scale].intensity = 0.3
    presets[PaintMode.add].intensity = 0.1
    presets[PaintMode.scale].intensity = 0.95

    return presets


class Model(Object):
    def __init__(self):
        self.mode_changed = Signal("mode changed")
        self.presets = make_presets()
        self.current_settings = None
        self.set_mode(PaintMode.replace)

    def set_mode(self, mode):
        self.current_settings = self.presets[mode]
        self.mode_changed.emit()

    def apply(self):
        flood_weights(session.state.currentLayer.layer, influences=session.state.currentLayer.layer.paint_targets, settings=self.current_settings)


def build_ui(parent):
    model = Model()
    ui_lock = UiLock()

    def build_mode_settings_group():
        def mode_row():
            row = QtWidgets.QVBoxLayout()

            group = QActionGroup(parent)

            actions = {}

            def create_mode_button(toolbar, mode, label, tooltip):
                a = QAction(label, parent)
                a.setToolTip(tooltip)
                a.setStatusTip(tooltip)
                a.setCheckable(True)
                actions[mode] = a
                group.addAction(a)

                @qt.on(a.toggled)
                @ui_lock.skip_if_updating
                def toggled(checked):
                    if checked:
                        model.set_mode(mode)
                        update_ui()

                toolbar.addAction(a)

            t = QtWidgets.QToolBar()
            create_mode_button(t, PaintMode.replace, "替换", "")
            create_mode_button(t, PaintMode.add, "添加", "")
            create_mode_button(t, PaintMode.scale, "减少", "")
            row.addWidget(t)

            t = QtWidgets.QToolBar()
            create_mode_button(t, PaintMode.smooth, "平滑", "")
            create_mode_button(t, PaintMode.sharpen, "锐化", "")
            row.addWidget(t)

            actions[model.current_settings.mode].setChecked(True)

            return row

        influences_limit = widgets.NumberSliderGroup(value_type=int, min_value=0, max_value=10)

        @signal.on(influences_limit.valueChanged)
        @ui_lock.skip_if_updating
        def influences_limit_changed():
            for _, v in model.presets.items():
                v.influences_limit = influences_limit.value()
            update_ui()

        intensity = widgets.NumberSliderGroup()

        @signal.on(intensity.valueChanged, qtParent=parent)
        @ui_lock.skip_if_updating
        def intensity_edited():
            model.current_settings.intensity = intensity.value()
            update_ui()

        iterations = widgets.NumberSliderGroup(value_type=int, min_value=1, max_value=100)

        @signal.on(iterations.valueChanged, qtParent=parent)
        @ui_lock.skip_if_updating
        def iterations_edited():
            model.current_settings.iterations = iterations.value()
            update_ui()

        fixed_influences = QtWidgets.QCheckBox("仅调整顶点现有影响物，防止周围权重扩散")
        fixed_influences.setToolTip(
            "启用此选项后，平滑-将仅调整每个顶点的现有影响物, "
            "而不会包含来自附近顶点的影响物，防止周围权重扩散"
        )

        volume_neighbours = QtWidgets.QCheckBox("平滑间隙和薄表面")
        volume_neighbours.setToolTip(
            "使用所有附近相邻的面，无论它们是否属于同一个曲面."
            "这将允许在间隙和薄曲面之间进行平滑."
        )

        limit_to_component_selection = QtWidgets.QCheckBox("在选择的组件中平滑")
        limit_to_component_selection.setToolTip("启用此选项后，仅在选定组件之间进行平滑")

        @qt.on(fixed_influences.stateChanged)
        @ui_lock.skip_if_updating
        def fixed_influences_changed(*_):
            model.current_settings.fixed_influences_per_vertex = fixed_influences.isChecked()

        @qt.on(limit_to_component_selection.stateChanged)
        @ui_lock.skip_if_updating
        def limit_to_component_selection_changed(*_):
            model.current_settings.limit_to_component_selection = limit_to_component_selection.isChecked()

        def update_ui():
            with ui_lock:
                widgets.set_paint_expo(intensity, model.current_settings.mode)

                intensity.set_value(model.current_settings.intensity)

                iterations.set_value(model.current_settings.iterations)
                iterations.set_enabled(model.current_settings.mode in [PaintMode.smooth, PaintMode.sharpen])

                fixed_influences.setEnabled(model.current_settings.mode in [PaintMode.smooth])
                fixed_influences.setChecked(model.current_settings.fixed_influences_per_vertex)

                limit_to_component_selection.setChecked(model.current_settings.limit_to_component_selection)
                limit_to_component_selection.setEnabled(fixed_influences.isEnabled())

                influences_limit.set_value(model.current_settings.influences_limit)

                volume_neighbours.setChecked(model.current_settings.use_volume_neighbours)
                volume_neighbours.setEnabled(model.current_settings.mode == PaintMode.smooth)

        settings_group = QtWidgets.QGroupBox("模式设置")
        layout = QtWidgets.QVBoxLayout()

        layout.addLayout(createTitledRow("模式:", mode_row()))
        layout.addLayout(createTitledRow("强度:", intensity.layout()))
        layout.addLayout(createTitledRow("迭代次数:", iterations.layout()))
        layout.addLayout(createTitledRow("影响物限制:", influences_limit.layout()))
        layout.addLayout(createTitledRow("平滑辅助:", fixed_influences))
        layout.addLayout(createTitledRow("体积平滑:", volume_neighbours))
        layout.addLayout(createTitledRow("隔离选中组件:", limit_to_component_selection))
        settings_group.setLayout(layout)

        update_ui()

        return settings_group

    def common_settings():
        layout = QtWidgets.QVBoxLayout()

        mirror = QtWidgets.QCheckBox("镜像")
        layout.addLayout(createTitledRow("", mirror))

        @qt.on(mirror.stateChanged)
        @ui_lock.skip_if_updating
        def mirror_changed(*_):
            for _, v in model.presets.items():
                v.mirror = mirror.isChecked()

        redistribute_removed_weight = QtWidgets.QCheckBox("分配给其它影响物")
        layout.addLayout(createTitledRow("移除的权重:", redistribute_removed_weight))

        @qt.on(redistribute_removed_weight.stateChanged)
        def redistribute_removed_weight_changed():
            for _, v in model.presets.items():
                v.distribute_to_other_influences = redistribute_removed_weight.isChecked()

        @signal.on(model.mode_changed, qtParent=layout)
        def update_ui():
            mirror.setChecked(model.current_settings.mirror)
            redistribute_removed_weight.setChecked(model.current_settings.distribute_to_other_influences)

        group = QtWidgets.QGroupBox("常用设置")
        group.setLayout(layout)

        update_ui()

        return group

    def apply_button():
        btn = QtWidgets.QPushButton("应用")
        btn.setToolTip("将设定操作应用于选中顶点")

        @qt.on(btn.clicked)
        def clicked():
            model.apply()

        return btn

    tab = TabSetup()
    tab.innerLayout.addWidget(build_mode_settings_group())
    tab.innerLayout.addWidget(common_settings())
    tab.innerLayout.addStretch()

    tab.lowerButtonsRow.addWidget(apply_button())

    @signal.on(session.events.targetChanged, qtParent=tab.tabContents)
    def update_tab_enabled():
        tab.tabContents.setEnabled(session.state.layersAvailable)

    update_tab_enabled()

    return tab.tabContents
