import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id: root
    width: Math.min(parent.width - 60, 700)
    height: Math.min(parent.height - 60, 660)
    onOpened: {
        if (shelf.tmdb.state.hasKey) queryInput.forceActiveFocus()
        else credentialInput.forceActiveFocus()
    }
    onAboutToHide: { shelf.tmdb.cancelSearch(); shelf.tmdb.cancelImport() }
    ColumnLayout {
        anchors.fill: parent
        spacing: 17
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: Theme.tr("Find a movie on TMDB"); color: Theme.text; font.pixelSize: 25; font.weight: Font.DemiBold }
                Text { text: Theme.tr("Choose a result, then check its details before saving."); color: Theme.secondary; font.pixelSize: 12 }
            }
            ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Cancel"); onClicked: root.close() }
        }
        ColumnLayout {
            visible: !shelf.tmdb.state.hasKey
            Layout.fillWidth: true
            spacing: 14
            Text { text: Theme.tr("Use your own TMDB key"); color: Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
            Text { text: Theme.tr("Your key is saved only in your user profile on this computer."); color: Theme.secondary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            Field { id: credentialInput; objectName: "tmdbSetupKey"; Layout.fillWidth: true; echoMode: TextInput.Password; placeholderText: Theme.tr("API key or Read Access Token"); onAccepted: saveKey.clicked() }
            RowLayout {
                Layout.fillWidth: true
                ActionButton { text: Theme.tr("Get a free TMDB key"); quiet: true; onClicked: Qt.openUrlExternally("https://www.themoviedb.org/settings/api") }
                Item { Layout.fillWidth: true }
                ActionButton { id: saveKey; objectName: "tmdbSetupSave"; text: Theme.tr("Save key"); primary: true; onClicked: { if (shelf.tmdb.saveCredential(credentialInput.text)) { credentialInput.text = ""; queryInput.forceActiveFocus() } } }
            }
        }
        ColumnLayout {
            visible: shelf.tmdb.state.hasKey
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 14
            RowLayout {
                Layout.fillWidth: true
                Glyph { name: "search"; ink: Theme.accent; width: 20; height: 20 }
                Field { id: queryInput; objectName: "tmdbQuery"; Layout.fillWidth: true; placeholderText: Theme.tr("Search movie titles on TMDB…"); onTextEdited: searchTimer.restart(); onAccepted: { searchTimer.stop(); shelf.tmdb.search(text) } }
                Timer { id: searchTimer; interval: 350; onTriggered: shelf.tmdb.search(queryInput.text) }
            }
            Text { visible: !!shelf.tmdb.state.error; text: shelf.tmdb.state.error; textFormat: Text.PlainText; color: Theme.danger; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            ListView {
                id: results
                objectName: "tmdbResults"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 7
                model: shelf.tmdb.state.results
                delegate: Button {
                    id: item
                    required property var modelData
                    width: ListView.view.width
                    height: 90
                    enabled: !shelf.tmdb.state.importing
                    hoverEnabled: true
                    onClicked: shelf.tmdb.importMovie(modelData.id)
                    background: Rectangle { radius: 11; color: item.hovered ? Theme.hover : Theme.elevated; border.color: item.activeFocus ? Theme.accent : "transparent"; Behavior on color { ColorAnimation { duration: Theme.duration } } }
                    contentItem: RowLayout {
                        spacing: 14
                        Image { Layout.preferredWidth: 48; Layout.preferredHeight: 72; source: item.modelData.posterUrl || ""; asynchronous: true; smooth: true; mipmap: true; fillMode: Image.PreserveAspectFit }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text { text: item.modelData.title; textFormat: Text.PlainText; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.fillWidth: true; elide: Text.ElideRight }
                            Text { text: item.modelData.year || Theme.tr("Release year unknown"); color: Theme.secondary; font.pixelSize: 12 }
                            Text { text: item.modelData.description || ""; textFormat: Text.PlainText; color: Theme.secondary; font.pixelSize: 11; Layout.fillWidth: true; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight }
                        }
                        Glyph { name: "arrow"; rotation: -90; width: 15; height: 15 }
                    }
                }
                ScrollBar.vertical: ScrollBar {}
            }
            RowLayout {
                Layout.fillWidth: true
                BusyIndicator { visible: shelf.tmdb.state.searching || shelf.tmdb.state.importing; running: visible; Layout.preferredWidth: 28; Layout.preferredHeight: 28 }
                Text { visible: shelf.tmdb.state.importing; text: Theme.tr("Loading movie details and poster…"); color: Theme.secondary; font.pixelSize: 12 }
                Text { visible: queryInput.text.trim().length >= 2 && !shelf.tmdb.state.searching && !shelf.tmdb.state.importing && !shelf.tmdb.state.error && shelf.tmdb.state.results.length === 0; text: Theme.tr("No TMDB results found."); color: Theme.secondary; font.pixelSize: 12 }
                Item { Layout.fillWidth: true }
            }
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.line }
        RowLayout {
            Layout.fillWidth: true
            Text { text: Theme.tr("TMDB results need your own API key."); color: Theme.secondary; font.pixelSize: 11 }
            Item { Layout.fillWidth: true }
            ActionButton { text: Theme.tr("Enter manually"); enabled: !shelf.tmdb.state.importing; onClicked: { root.close(); shelf.editMovie(0) } }
        }
    }
}
