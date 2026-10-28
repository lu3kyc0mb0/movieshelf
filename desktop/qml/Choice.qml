import QtQuick
import QtQuick.Controls

ComboBox {
    id: control
    implicitHeight: 40
    implicitWidth: 190
    leftPadding: 12
    rightPadding: 30
    font.pixelSize: 13
    contentItem: Text { text: control.displayText; textFormat: Text.PlainText; color: Theme.text; font: control.font; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
    background: Rectangle { radius: 10; color: control.hovered ? Theme.hover : Theme.elevated; border.width: control.activeFocus ? 2 : 0; border.color: Theme.accent }
    indicator: Glyph { name: "arrow"; width: 15; height: 15; x: control.width - 23; y: (control.height - height) / 2 }
    delegate: ItemDelegate {
        required property int index
        required property var modelData
        width: control.width
        text: control.textRole ? modelData[control.textRole] : modelData
        highlighted: control.highlightedIndex === index
        contentItem: Text { text: parent.text; textFormat: Text.PlainText; color: Theme.text; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter; font.pixelSize: 13 }
        background: Rectangle { radius: 7; color: parent.highlighted ? Theme.selected : "transparent" }
    }
    popup: Popup {
        y: control.height + 5
        width: control.width
        padding: 5
        implicitHeight: Math.min(contentItem.implicitHeight + 10, 300)
        contentItem: ListView { clip: true; implicitHeight: contentHeight; model: control.popup.visible ? control.delegateModel : null; currentIndex: control.highlightedIndex; ScrollIndicator.vertical: ScrollIndicator {} }
        background: Rectangle { color: Theme.surface; border.color: Theme.line; radius: 12 }
    }
}
