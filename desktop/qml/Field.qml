import QtQuick
import QtQuick.Controls

TextField {
    id: control
    implicitHeight: Theme.px(42)
    color: Theme.text
    placeholderTextColor: Theme.secondary
    selectionColor: Theme.accent
    selectedTextColor: Theme.accentText
    font.pixelSize: Theme.px(14)
    leftPadding: 13
    rightPadding: 13
    selectByMouse: true
    background: Rectangle {
        color: Theme.elevated
        radius: 10
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Theme.accent : Theme.line
        Behavior on border.color { ColorAnimation { duration: Theme.duration } }
    }
}
