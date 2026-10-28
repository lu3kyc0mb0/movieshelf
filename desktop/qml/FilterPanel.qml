import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    implicitHeight: layout.implicitHeight + 28
    color: Theme.surface
    radius: 14
    border.color: Theme.line
    component FilterNumber: ColumnLayout {
        id: numberControl
        property string caption
        property string filterKey
        property int maximum: 2100
        spacing: 6
        Text { text: Theme.tr(parent.caption); color: Theme.secondary; font.pixelSize: 11 }
        Field {
            Layout.fillWidth: true
            Layout.minimumWidth: 70
            implicitHeight: 35
            placeholderText: Theme.tr("Any")
            text: shelf.state.filters[parent.filterKey] ? String(shelf.state.filters[parent.filterKey]) : ""
            validator: IntValidator { bottom: 0; top: numberControl.maximum }
            onEditingFinished: shelf.setFilter(parent.filterKey, parseInt(text) || 0)
        }
    }
    ColumnLayout {
        id: layout
        anchors { fill: parent; margins: 14 }
        spacing: 10
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            FilterNumber { caption: "From year"; filterKey: "yearFrom"; Layout.fillWidth: true }
            FilterNumber { caption: "To year"; filterKey: "yearTo"; Layout.fillWidth: true }
            FilterNumber { caption: "Min rating"; filterKey: "ratingFrom"; maximum: 10; Layout.fillWidth: true }
            FilterNumber { caption: "Max rating"; filterKey: "ratingTo"; maximum: 10; Layout.fillWidth: true }
        }
        RowLayout {
            Layout.fillWidth: true
            Choice { Layout.fillWidth: true; Layout.preferredWidth: 120; model: [Theme.tr("All statuses"), Theme.tr("Want to watch"), Theme.tr("Watched")]; currentIndex: ["", "watchlist", "watched"].indexOf(shelf.state.filters.status || ""); onActivated: shelf.setFilter("status", ["", "watchlist", "watched"][currentIndex]) }
            Choice { Layout.fillWidth: true; Layout.preferredWidth: 120; model: [Theme.tr("Favorite") + ": " + Theme.tr("Any"), Theme.tr("Favorites only"), Theme.tr("Not favorites")]; currentIndex: ["", "yes", "no"].indexOf(shelf.state.filters.favorite || ""); onActivated: shelf.setFilter("favorite", ["", "yes", "no"][currentIndex]) }
            Choice { Layout.fillWidth: true; Layout.preferredWidth: 120; model: [Theme.tr("Any genre")].concat(shelf.state.genres); currentIndex: shelf.state.filters.genre ? shelf.state.genres.indexOf(shelf.state.filters.genre) + 1 : 0; onActivated: shelf.setFilter("genre", currentIndex ? shelf.state.genres[currentIndex - 1] : "") }
        }
        RowLayout {
            Layout.fillWidth: true
            Choice { Layout.fillWidth: true; model: [Theme.tr("Any tag")].concat(shelf.state.tags); currentIndex: shelf.state.filters.tag ? shelf.state.tags.indexOf(shelf.state.filters.tag) + 1 : 0; onActivated: shelf.setFilter("tag", currentIndex ? shelf.state.tags[currentIndex - 1] : "") }
            Choice { Layout.fillWidth: true; model: [Theme.tr("Any collection")].concat(shelf.state.collections.map(c => c.name)); currentIndex: shelf.state.filters.collection ? shelf.state.collections.findIndex(c => c.id === shelf.state.filters.collection) + 1 : 0; onActivated: shelf.setFilter("collection", currentIndex ? shelf.state.collections[currentIndex - 1].id : "") }
            ActionButton { text: Theme.tr("Reset filters"); quiet: true; onClicked: shelf.resetFilters() }
        }
    }
}
