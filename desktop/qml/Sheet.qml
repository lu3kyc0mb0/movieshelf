import QtQuick
import QtQuick.Controls

Popup {
    id: root
    parent: Overlay.overlay
    anchors.centerIn: parent
    modal: true
    focus: true
    padding: 28
    closePolicy: Popup.CloseOnEscape
    background: Rectangle { color: Theme.surface; radius: 22; border.color: Theme.line; antialiasing: true }
    Overlay.modal: Rectangle { color: Theme.dark ? "#99090a10" : "#66303346"; Behavior on opacity { NumberAnimation { duration: Theme.duration } } }
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.duration }
        NumberAnimation { property: "scale"; from: 0.97; to: 1; duration: Theme.duration; easing.type: Easing.OutCubic }
    }
    exit: Transition { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.duration } }
}
