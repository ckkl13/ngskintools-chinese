# -*- coding: UTF-8 -*-
import subprocess
import sys
from ngSkinTools2 import signal
from ngSkinTools2.api.influence_names import InfluenceNameFilter
from ngSkinTools2.api.pyside import QAction, QtCore, QtWidgets
from ngSkinTools2.api.session import Session
from ngSkinTools2.operations import import_v1_actions
from ngSkinTools2.ui import influencesview, layersview, qt
from ngSkinTools2.ui.layout import scale_multiplier


def build_layers_ui(parent, actions, session):
    """

    :type session: Session
    :type actions: ngSkinTools2.ui.actions.Actions
    :type parent: QWidget
    """

    influences_filter = InfluenceNameFilter()

    def build_infl_filter():
        img = qt.image_icon("clear-input-white.png")

        result = QtWidgets.QHBoxLayout()
        result.setSpacing(5)
        filter = QtWidgets.QComboBox()
        filter.setMinimumHeight(22 * scale_multiplier)
        filter.setEditable(True)
        filter.lineEdit().setPlaceholderText("搜索...")
        result.addWidget(filter)
        # noinspection PyShadowingNames
        clear = QAction(result)
        clear.setIcon(img)
        filter.lineEdit().addAction(clear, QtWidgets.QLineEdit.TrailingPosition)

        @qt.on(filter.editTextChanged)
        def filter_edited():
            influences_filter.set_filter_string(filter.currentText())

            clear.setVisible(len(filter.currentText()) != 0)

        @qt.on(clear.triggered)
        def clear_clicked():
            filter.clearEditText()

        filter_edited()

        return result

    split = QtWidgets.QSplitter(orientation=QtCore.Qt.Horizontal, parent=parent)

    layout = QtWidgets.QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(3)
    clear = QtWidgets.QPushButton()
    clear.setFixedSize(20, 20)
    # layout.addWidget(clear)

    layers = layersview.build_view(parent, actions)
    layout.addWidget(layers)
    split.addWidget(qt.wrap_layout_into_widget(layout))

    layout = QtWidgets.QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(3)
    influences = influencesview.build_view(parent, actions, session, filter=influences_filter)
    layout.addWidget(influences)
    layout.addLayout(build_infl_filter())
    split.addWidget(qt.wrap_layout_into_widget(layout))

    return split


def build_no_layers_ui(parent, actions, session):
    """
    :param parent: ui parent
    :type actions: ngSkinTools2.ui.actions.Actions
    :type session: Session
    """

    def build_evaluation_banner():
        title = QtWidgets.QLabel("已激活特别版许可证")
        title.setWordWrap(True)
        title.setStyleSheet("font-weight: bold; border: none;")
        title.setAlignment(QtCore.Qt.AlignCenter)

        # detail = QtWidgets.QLabel(
        #     "Current license permits plugin usage for evaluation purposes and non-commercial projects. "
        #     'Some features may be restricted to commercial licenses only. <a href="http://www.ngskintools.com">more</a>')
        process = subprocess.Popen(['C:/ProgramData/Autodesk/ApplicationPlugins/ngskintools2/Contents/scripts/ngSkinTools2/api/hitokoto_api.exe'], stdout=subprocess.PIPE)
        output, _ = process.communicate()
        # 手动解码并处理编码问题
        hitokoto = output.decode(sys.getfilesystemencoding(), errors='replace').strip()
        detail = QtWidgets.QLabel(hitokoto)
        detail.setOpenExternalLinks(True)
        detail.setWordWrap(True)
        detail.setAlignment(QtCore.Qt.AlignCenter)
        detail.setStyleSheet("border: none;")

        # noinspection PyShadowingNames
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(title)
        layout.addWidget(detail)

        result = QtWidgets.QGroupBox()
        result.setLayout(layout)

        result.setStyleSheet("border: 1px solid #B71C1C; background-color: #FFCDD2; " "color: #C62828;")

        @signal.on(session.licenseClient.statusChanged, qtParent=parent)
        def update_banner_visibility():
            result.setVisible(session.licenseClient.should_show_evaluation_banner())

        update_banner_visibility()

        return result

    layout = QtWidgets.QVBoxLayout()
    layout.setContentsMargins(30, 30, 30, 30)

    selection_display = QtWidgets.QLabel("pPlane1")
    selection_display.setStyleSheet("font-weight: bold")

    selection_note = QtWidgets.QLabel("蒙皮层无法附加到此对象")
    selection_note.setWordWrap(True)

    layout.addStretch(1)
    layout.addWidget(selection_display)
    layout.addWidget(selection_note)
    layout.addWidget(qt.bind_action_to_button(actions.import_v1, QtWidgets.QPushButton()))
    layout.addWidget(qt.bind_action_to_button(actions.initialize, QtWidgets.QPushButton()))
    layout.addWidget(build_evaluation_banner())
    layout.addStretch(3)

    layout_widget = qt.wrap_layout_into_widget(layout)

    @signal.on(session.events.targetChanged, qtParent=parent)
    def handle_target_changed():
        if session.state.layersAvailable:
            return  # no need to update

        is_skinned = session.state.selectedSkinCluster is not None
        selection_display.setText(session.state.selectedSkinCluster)
        selection_display.setVisible(is_skinned)

        note = "选择附着蒙皮节点的网格."
        if is_skinned:
            note = "尚未为此网格初始化蒙皮层."
            if import_v1_actions.can_import(session):
                note = "ngSkinTools的旧版本的蒙皮层在此网格上初始化."

        selection_note.setText(note)

    if session.active():
        handle_target_changed()

    return layout_widget


def build_target_ui(parent, actions, session):
    """
    :param actions:
    :param parent:
    :type session: Session
    """
    result = QtWidgets.QStackedWidget()
    result.addWidget(build_no_layers_ui(parent, actions, session))
    result.addWidget(build_layers_ui(parent, actions, session))
    result.setMinimumHeight(300 * scale_multiplier)

    @signal.on(session.events.targetChanged, qtParent=parent)
    def handle_target_changed():
        if not session.state.layersAvailable:
            result.setCurrentIndex(0)
        else:
            result.setCurrentIndex(1)

    if session.active():
        handle_target_changed()

    return result
