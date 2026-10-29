import QtQuick
import QtQuick.Controls

ActionButton {
    id: root
    property string sequence: ""
    property bool recording: false
    signal recorded(string value)
    text: recording ? Theme.tr("Press a combination…") : sequence || Theme.tr("Not assigned")
    foreground: recording ? Theme.accent : Theme.text
    Accessible.name: Theme.tr("Record shortcut") + ": " + text
    onClicked: { recording = true; forceActiveFocus() }
    onActiveFocusChanged: if (!activeFocus) recording = false
    Keys.onShortcutOverride: event => { if (recording) event.accepted = true }
    Keys.onPressed: event => {
        if (!recording) return
        event.accepted = true
        if (event.key === Qt.Key_Escape) { recording = false; return }
        if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) { recording = false; event.accepted = false; return }
        if (event.key === Qt.Key_Backspace || event.key === Qt.Key_Delete) { recorded(""); recording = false; return }
        let value = shelf.keySequence(event.key, event.modifiers)
        if (value) { recorded(value); recording = false }
    }
}
