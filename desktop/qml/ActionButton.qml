import QtQuick
import QtQuick.Controls

Button {
    id: control
    property string glyph: ""
    property bool primary: false
    property bool quiet: false
    property bool destructive: false
    property color foreground: primary ? "white" : destructive ? Theme.danger : Theme.text
    implicitHeight: 40
    implicitWidth: Math.max(40, contentItem.implicitWidth + (text ? 28 : 18))
    padding: 0
    hoverEnabled: true
    font.pixelSize: 13
    font.weight: Font.DemiBold
    opacity: enabled ? 1 : 0.45
    scale: down ? 0.97 : 1
    Behavior on scale { NumberAnimation { duration: Theme.duration; easing.type: Easing.OutCubic } }
    background: Rectangle {
        radius: 11
        color: control.primary ? (control.down ? "#0063d5" : control.hovered ? "#268dff" : "#007aff")
                              : control.hovered ? Theme.hover : control.quiet ? "transparent" : Theme.elevated
        border.width: control.activeFocus ? 2 : 0
        border.color: Theme.accent
        Behavior on color { ColorAnimation { duration: Theme.duration } }
    }
    contentItem: Item {
        implicitWidth: row.width
        implicitHeight: 24
        Row {
            id: row
            anchors.centerIn: parent
            spacing: 8
            Glyph { visible: control.glyph !== ""; name: control.glyph; ink: control.foreground; width: 19; height: 19; anchors.verticalCenter: parent.verticalCenter }
            Text { visible: control.text !== ""; text: control.text; textFormat: Text.PlainText; color: control.foreground; font: control.font; anchors.verticalCenter: parent.verticalCenter }
        }
    }
    ToolTip.visible: hovered && text === "" && Accessible.name !== ""
    ToolTip.text: Accessible.name
    ToolTip.delay: 600
}
