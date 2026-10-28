import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id: root
    width: Math.min(parent.width - 60, 570)
    height: Math.min(parent.height - 60, 620)
    onOpened: {
        appearance.currentIndex = shelf.state.preferences.theme === "dark" ? 1 : 0
        language.currentIndex = ["en", "ru", "kk"].indexOf(shelf.state.preferences.language)
        animations.checked = shelf.state.preferences.animations
        statistics.checked = shelf.state.preferences.show_statistics
        posterSize.value = shelf.state.preferences.card_size
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 22
        RowLayout {
            Layout.fillWidth: true
            Text { text: Theme.tr("Settings"); color: Theme.text; font.pixelSize: 27; font.weight: Font.DemiBold; Layout.fillWidth: true }
            ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Cancel"); onClicked: root.close() }
        }
        GridLayout {
            columns: 2
            rowSpacing: 20
            columnSpacing: 24
            Layout.fillWidth: true
            Text { text: Theme.tr("Appearance"); color: Theme.secondary }
            Choice { id: appearance; objectName: "themeChoice"; Layout.fillWidth: true; model: [Theme.tr("Light"), Theme.tr("Dark")] }
            Text { text: Theme.tr("Language"); color: Theme.secondary }
            Choice { id: language; objectName: "languageChoice"; Layout.fillWidth: true; model: ["English", "Русский", "Қазақша"] }
            Text { text: Theme.tr("Poster size"); color: Theme.secondary }
            ScaleSlider { id: posterSize; Layout.fillWidth: true; from: 155; to: 245; stepSize: 5; Accessible.name: Theme.tr("Poster size") }
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.line }
        Toggle { id: animations; text: Theme.tr("Smooth transitions"); Layout.fillWidth: true }
        Toggle { id: statistics; text: Theme.tr("Show collection statistics"); Layout.fillWidth: true }
        ActionButton { text: Theme.tr("Export library backup…"); glyph: "folder"; onClicked: shelf.exportBackup() }
        Item { Layout.fillHeight: true }
        RowLayout {
            Layout.fillWidth: true
            Text { text: "MovieShelf " + Qt.application.version; color: Theme.secondary; font.pixelSize: 11 }
            Item { Layout.fillWidth: true }
            ActionButton { text: Theme.tr("Cancel"); quiet: true; onClicked: root.close() }
            ActionButton { objectName: "saveSettingsButton"; text: Theme.tr("Save and apply"); primary: true; onClicked: { if (shelf.saveSettings({theme: appearance.currentIndex ? "dark" : "light", language: ["en", "ru", "kk"][language.currentIndex], animations: animations.checked, show_statistics: statistics.checked, card_size: Math.round(posterSize.value)})) root.close() } }
        }
    }
}
