# -*- coding: UTF-8 -*-
from ngSkinTools2 import api, signal
from ngSkinTools2.api.pyside import QtWidgets
from ngSkinTools2.ui.options import PersistentValue

filter_normal_json = 'JSON files(*.json)'
filter_compressed = 'Compressed JSON(*.json.gz)'
file_dialog_filters = ";;".join([filter_normal_json, filter_compressed])

format_map = {
    filter_normal_json: api.FileFormat.JSON,
    filter_compressed: api.FileFormat.CompressedJSON,
}

default_filter = PersistentValue("default_import_filter", default_value=api.FileFormat.JSON)


def buildAction_export(session, parent):
    from ngSkinTools2.ui import actions

    def export_callback():
        file_name, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            parent, "导出为Json", filter=file_dialog_filters, selectedFilter=default_filter.get()
        )
        if not file_name:
            return

        default_filter.set(selected_filter)

        if session.state.layersAvailable:
            api.export_json(session.state.selectedSkinCluster, file_name, format=format_map[selected_filter])

    result = actions.define_action(
        parent,
        "将图层导出为Json…",
        callback=export_callback,
        tooltip="保存图层信息到外部文件，适合导入权重到不同的场景/网格",
    )

    @signal.on(session.events.targetChanged, qtParent=parent)
    def update_to_target():
        result.setEnabled(session.state.layersAvailable)

    update_to_target()

    return result


def buildAction_import(session, parent, file_dialog_func=None):
    from ngSkinTools2.ui import actions
    from ngSkinTools2.ui.transferDialog import LayersTransfer, UiModel, open

    def default_file_dialog_func():
        file_name, selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            parent, "从Json导入", filter=file_dialog_filters, selectedFilter=default_filter.get()
        )
        if file_name:
            default_filter.set(selected_filter)
        return file_name, selected_filter

    if file_dialog_func is None:
        file_dialog_func = default_file_dialog_func

    def transfer_dialog(transfer):
        model = UiModel()
        model.transfer = transfer
        open(parent, model)

    def import_callback():
        if session.state.selectedSkinCluster is None:
            return

        file_name, selected_format = file_dialog_func()
        if not file_name:
            return

        t = LayersTransfer()
        t.load_source_from_file(file_name, format=format_map[selected_format])
        t.target = session.state.selectedSkinCluster
        t.customize_callback = transfer_dialog
        t.execute()

    result = actions.define_action(parent, "从Json中导入图层…", callback=import_callback, tooltip="装载以前导出的权重")

    @signal.on(session.events.targetChanged, qtParent=parent)
    def update():
        result.setEnabled(session.state.selectedSkinCluster is not None)

    update()

    return result
