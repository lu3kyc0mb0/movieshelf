import QtQuick
import QtQuick.Effects

Item {
    id: root
    property url source: ""
    property var crop: ({zoom: 1, x: 0, y: 0, mode: "fill"})
    property bool editable: false
    property real cornerRadius: 13
    signal dropped(string url)
    signal repositioned(real cropX, real cropY)
    readonly property bool ready: artwork.status === Image.Ready
    Rectangle {
        id: mask
        anchors.fill: parent
        radius: root.cornerRadius
        color: "white"
        layer.enabled: true
        visible: false
    }
    Item {
        id: frame
        anchors.fill: parent
        layer.enabled: true
        layer.effect: MultiEffect { maskEnabled: true; maskSource: mask; maskThresholdMin: 0.5; maskSpreadAtMin: 1 }
        Rectangle { anchors.fill: parent; color: Theme.elevated }
        Image {
            id: artwork
            source: root.source
            asynchronous: true
            autoTransform: true
            smooth: true
            mipmap: true
            sourceSize: Qt.size(1536, 1536)
            readonly property real factor: (root.crop.mode === "fit" ? Math.min(frame.width / Math.max(1, implicitWidth), frame.height / Math.max(1, implicitHeight)) : Math.max(frame.width / Math.max(1, implicitWidth), frame.height / Math.max(1, implicitHeight))) * root.crop.zoom
            width: implicitWidth * factor
            height: implicitHeight * factor
            x: (frame.width - width) / 2 + root.crop.x * Math.abs(frame.width - width) / 2
            y: (frame.height - height) / 2 + root.crop.y * Math.abs(frame.height - height) / 2
            opacity: status === Image.Ready ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: Theme.duration } }
        }
        Column {
            anchors.centerIn: parent
            spacing: 14
            visible: !root.ready
            Glyph { name: "image"; width: 36; height: 36; anchors.horizontalCenter: parent.horizontalCenter }
            Text { text: Theme.tr("NO ARTWORK\nAdd your own poster"); color: Theme.secondary; font.pixelSize: Theme.px(12); horizontalAlignment: Text.AlignHCenter }
        }
        Rectangle { anchors.fill: parent; color: "#55007aff"; visible: drop.containsDrag }
    }
    MouseArea {
        anchors.fill: parent
        enabled: root.editable
        cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
        property real startX
        property real startY
        property real cropX
        property real cropY
        onPressed: mouse => { startX = mouse.x; startY = mouse.y; cropX = root.crop.x; cropY = root.crop.y }
        onPositionChanged: mouse => {
            if (!pressed) return
            let dx = Math.abs(artwork.width - root.width)
            let dy = Math.abs(artwork.height - root.height)
            root.repositioned(dx > 1 ? Math.max(-1, Math.min(1, cropX + (mouse.x - startX) * 2 / dx)) : cropX,
                              dy > 1 ? Math.max(-1, Math.min(1, cropY + (mouse.y - startY) * 2 / dy)) : cropY)
        }
    }
    DropArea {
        id: drop
        anchors.fill: parent
        enabled: root.editable
        onEntered: drag => { drag.accepted = drag.hasUrls }
        onDropped: drop => { if (drop.hasUrls) { root.dropped(drop.urls[0].toString()); drop.acceptProposedAction() } }
    }
}
