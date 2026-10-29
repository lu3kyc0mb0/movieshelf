import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    property var model: []
    property int currentIndex: 0
    signal activated(int index)
    implicitHeight: Theme.px(43)
    radius: 11
    color: Theme.elevated
    Rectangle {
        x: 4 + root.currentIndex * (root.width - 8) / Math.max(1, root.model.length)
        y: 4
        width: (root.width - 8) / Math.max(1, root.model.length)
        height: root.height - 8
        color: Theme.surface
        radius: 8
        Behavior on x { NumberAnimation { duration: Theme.duration; easing.type: Easing.OutCubic } }
    }
    Row {
        anchors.fill: parent
        anchors.margins: 4
        Repeater {
            model: root.model
            delegate: Button {
                id: tab
                required property string modelData
                required property int index
                width: (root.width - 8) / Math.max(1, root.model.length)
                height: root.height - 8
                hoverEnabled: true
                Accessible.role: Accessible.PageTab
                Accessible.selected: root.currentIndex === index
                onClicked: root.activated(index)
                background: Rectangle {
                    radius: 8
                    color: Theme.hover
                    opacity: tab.hovered && root.currentIndex !== tab.index ? 0.5 : 0
                    Behavior on opacity { NumberAnimation { duration: Theme.duration } }
                }
                Rectangle { anchors.fill: parent; radius: 8; color: "transparent"; border.width: tab.activeFocus ? 1 : 0; border.color: Theme.accent }
                contentItem: Text { text: tab.modelData; color: root.currentIndex === tab.index ? Theme.text : Theme.secondary; font.pixelSize: Theme.px(13); horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
            }
        }
    }
}
