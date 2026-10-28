import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id: root
    width: Math.min(parent.width - 60, 600)
    height: Math.min(parent.height - 60, 700)
    onOpened: {
        appearance.currentIndex = shelf.state.preferences.theme === "dark" ? 1 : 0
        language.currentIndex = ["en", "ru", "kk"].indexOf(shelf.state.preferences.language)
        animations.checked = shelf.state.preferences.animations
        statistics.checked = shelf.state.preferences.show_statistics
        posterSize.value = shelf.state.preferences.card_size
        credential.text = ""
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 16
        RowLayout {
            Layout.fillWidth: true
            Text { text: Theme.tr("Settings"); color: Theme.text; font.pixelSize: 27; font.weight: Font.DemiBold; Layout.fillWidth: true }
            ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Cancel"); onClicked: root.close() }
        }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: parent.width
                spacing: 18
                GridLayout {
                    columns: 2
                    rowSpacing: 18
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
                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.line }
                Text { text: Theme.tr("TMDB connection"); color: Theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                Text { text: Theme.tr("Use your own API key or Read Access Token. It stays in this user's profile and is not included in library backups."); color: Theme.secondary; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Field { id: credential; objectName: "tmdbCredential"; Layout.fillWidth: true; echoMode: TextInput.Password; placeholderText: shelf.tmdb.state.hasKey ? Theme.tr("Personal key saved — leave blank to keep it") : Theme.tr("API key or Read Access Token") }
                RowLayout {
                    Layout.fillWidth: true
                    ActionButton { text: Theme.tr("Get a free TMDB key"); quiet: true; onClicked: Qt.openUrlExternally("https://www.themoviedb.org/settings/api") }
                    Item { Layout.fillWidth: true }
                    ActionButton { visible: shelf.tmdb.state.hasKey; text: Theme.tr("Remove key"); destructive: true; quiet: true; onClicked: shelf.tmdb.clearCredential() }
                    ActionButton { text: Theme.tr("Save key"); enabled: credential.text.trim().length > 0; onClicked: { if (shelf.tmdb.saveCredential(credential.text)) credential.text = "" } }
                }
                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.line }
                Text { text: Theme.tr("About & credits"); color: Theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                RowLayout {
                    Layout.fillWidth: true
                    Image { source: Qt.resolvedUrl("../assets/tmdb-logo.svg"); Layout.preferredWidth: 47; Layout.preferredHeight: 35; fillMode: Image.PreserveAspectFit; smooth: true }
                    Text { text: "TMDB"; color: Theme.secondary; font.pixelSize: 13; font.weight: Font.DemiBold }
                    Item { Layout.fillWidth: true }
                }
                Text { text: "This product uses the TMDB API but is not endorsed or certified by TMDB."; color: Theme.secondary; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                ActionButton { text: "themoviedb.org"; quiet: true; onClicked: Qt.openUrlExternally("https://www.themoviedb.org") }
            }
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.line }
        RowLayout {
            Layout.fillWidth: true
            Text { text: "MovieShelf " + Qt.application.version; color: Theme.secondary; font.pixelSize: 11 }
            Item { Layout.fillWidth: true }
            ActionButton { text: Theme.tr("Cancel"); quiet: true; onClicked: root.close() }
            ActionButton { objectName: "saveSettingsButton"; text: Theme.tr("Save and apply"); primary: true; onClicked: { if (shelf.saveSettings({theme: appearance.currentIndex ? "dark" : "light", language: ["en", "ru", "kk"][language.currentIndex], animations: animations.checked, show_statistics: statistics.checked, card_size: Math.round(posterSize.value)})) root.close() } }
        }
    }
}
