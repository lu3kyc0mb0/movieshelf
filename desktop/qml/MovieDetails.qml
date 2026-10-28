import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Sheet {
    id: root
    width: Math.min(parent.width - 60, 880)
    height: Math.min(parent.height - 60, 660)
    property var movie: shelf.detail
    ColumnLayout {
        anchors.fill: parent
        spacing: 24
        RowLayout {
            Layout.fillWidth: true
            Text { text: Theme.tr("Movie details"); color: Theme.secondary; font.pixelSize: 13; Layout.fillWidth: true }
            ActionButton { glyph: "close"; quiet: true; Accessible.name: Theme.tr("Done"); onClicked: root.close() }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 32
            Poster { Layout.preferredWidth: 240; Layout.preferredHeight: 360; Layout.alignment: Qt.AlignTop; source: root.movie.posterUrl || ""; crop: root.movie.poster_crop || ({zoom: 1, x: 0, y: 0, mode: "fill"}) }
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 18
                    Text { text: root.movie.title || ""; textFormat: Text.PlainText; color: Theme.text; font.pixelSize: 30; font.weight: Font.DemiBold; font.letterSpacing: -0.8; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: (root.movie.year || "") + "  ·  ID #" + (root.movie.id || ""); color: Theme.secondary; font.pixelSize: 14 }
                    RowLayout {
                        spacing: 14
                        Text { text: Theme.tr(root.movie.status === "watched" ? "Watched" : "Want to watch"); color: Theme.accent; font.pixelSize: 13 }
                        Glyph { name: "favorite"; visible: root.movie.favorite || false; ink: Theme.accent; width: 17; height: 17 }
                    }
                    Text { text: root.movie.rating ? "★ " + root.movie.rating + " / 10" : Theme.tr("Not rated"); color: Theme.gold; font.pixelSize: 20; font.weight: Font.DemiBold }
                    Text { visible: !!root.movie.genresText; text: root.movie.genresText || ""; color: Theme.secondary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { visible: !!root.movie.description; text: root.movie.description || ""; color: Theme.text; font.pixelSize: 14; lineHeight: 1.4; wrapMode: Text.WordWrap; Layout.fillWidth: true; textFormat: Text.PlainText }
                    Rectangle { Layout.fillWidth: true; height: 1; color: Theme.line }
                    Text { text: Theme.tr("My review"); color: Theme.secondary; font.pixelSize: 12; font.weight: Font.DemiBold }
                    Text { text: root.movie.review || Theme.tr("No written review yet."); color: Theme.text; font.pixelSize: 14; lineHeight: 1.4; wrapMode: Text.WordWrap; Layout.fillWidth: true; textFormat: Text.PlainText }
                    Text { visible: !!root.movie.tagsText; text: root.movie.tagsText || ""; color: Theme.secondary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            ActionButton { text: Theme.tr("Done"); onClicked: root.close() }
            ActionButton { text: Theme.tr("Edit movie"); glyph: "edit"; primary: true; onClicked: shelf.editMovie(root.movie.id) }
        }
    }
}
