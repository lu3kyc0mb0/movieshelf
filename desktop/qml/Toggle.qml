import QtQuick
import QtQuick.Controls

CheckBox {
    id: control
    implicitHeight: Theme.px(36)
    spacing: 10
    font.pixelSize: Theme.px(14)
    indicator: Rectangle {
        width: 20; height: 20; radius: 6
        x: control.leftPadding; y: (control.height - height) / 2
        color: control.checked ? Theme.accent : Theme.elevated
        border.color: control.activeFocus ? Theme.accent : control.checked ? Theme.accent : Theme.secondary
        Glyph { anchors.centerIn: parent; width: 15; height: 15; name: "check"; ink: Theme.accentText; visible: control.checked }
    }
    contentItem: Text { text: control.text; color: Theme.text; font: control.font; verticalAlignment: Text.AlignVCenter; leftPadding: control.indicator.width + control.spacing; wrapMode: Text.WordWrap }
}
