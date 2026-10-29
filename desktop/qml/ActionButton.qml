import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: control
    property string glyph: ""
    property bool primary: false
    property bool quiet: false
    property bool destructive: false
    property bool alignLeft: false
    property color foreground: primary ? Theme.accentText : destructive ? Theme.danger : Theme.text
    implicitHeight: Theme.px(40)
    implicitWidth: Math.max(40, contentItem.implicitWidth + (text ? 28 : 18))
    padding: 0
    hoverEnabled: true
    font.pixelSize: Theme.px(13)
    font.weight: Font.DemiBold
    opacity: enabled ? 1 : 0.45
    scale: down ? 0.97 : 1
    Behavior on scale { NumberAnimation { duration: Theme.duration; easing.type: Easing.OutCubic } }
    background: Rectangle {
        radius: 11
        color: control.primary ? (control.down ? Qt.darker(Theme.accent, 1.15) : control.hovered ? Qt.lighter(Theme.accent, 1.12) : Theme.accent)
                              : control.quiet ? Qt.rgba(Theme.hover.r, Theme.hover.g, Theme.hover.b, control.hovered ? 1 : 0) : control.hovered ? Theme.hover : Theme.elevated
        border.width: control.activeFocus ? 2 : 0
        border.color: Theme.accent
        Behavior on color { ColorAnimation { duration: Theme.duration } }
    }
    contentItem: Item {
        implicitWidth: label.implicitWidth + (control.glyph !== "" ? 27 : 0)
        implicitHeight: Theme.px(24)
        RowLayout {
            id: row
            anchors.fill: parent
            anchors.leftMargin: control.text ? 12 : 0
            anchors.rightMargin: control.text ? 12 : 0
            spacing: 8
            Glyph { visible: control.glyph !== ""; name: control.glyph; ink: control.foreground; Layout.preferredWidth: 19; Layout.preferredHeight: 19; Layout.alignment: Qt.AlignCenter }
            Text { id: label; visible: control.text !== ""; text: control.text; textFormat: Text.PlainText; color: control.foreground; font: control.font; Layout.fillWidth: true; horizontalAlignment: control.alignLeft ? Text.AlignLeft : Text.AlignHCenter; elide: Text.ElideRight }
        }
    }
    ToolTip.visible: hovered && text === "" && Accessible.name !== ""
    ToolTip.text: Accessible.name
    ToolTip.delay: 600
}
