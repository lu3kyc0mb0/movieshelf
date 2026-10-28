import QtQuick
import QtQuick.Controls

ScrollView {
    id: root
    property alias text: input.text
    property alias placeholderText: input.placeholderText
    signal edited(string value)
    clip: true
    implicitHeight: 160
    contentWidth: availableWidth
    background: Rectangle { radius: 11; color: Theme.elevated; border.color: input.activeFocus ? Theme.accent : Theme.line; border.width: input.activeFocus ? 2 : 1 }
    TextArea {
        id: input
        color: Theme.text
        placeholderTextColor: Theme.secondary
        selectionColor: Theme.accent
        selectedTextColor: "white"
        font.pixelSize: 14
        wrapMode: TextEdit.Wrap
        selectByMouse: true
        padding: 13
        textFormat: TextEdit.PlainText
        onTextChanged: root.edited(text)
    }
}
