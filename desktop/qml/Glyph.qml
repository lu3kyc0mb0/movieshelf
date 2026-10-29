import QtQuick
import QtQuick.Shapes

Item {
    id: root
    property string name: "library"
    property color ink: Theme.secondary
    readonly property var paths: ({
        library: "M3 4h7v7H3z M14 4h7v7h-7z M3 15h7v6H3z M14 15h7v6h-7z",
        watchlist: "M6 3h12v19l-6-4-6 4z",
        watched: "M20 11v2a8 8 0 1 1-5-8 M9 11l3 3 9-10",
        favorite: "M12 21S2 15 2 8a5 5 0 0 1 10-1 5 5 0 0 1 10 1c0 7-10 13-10 13z",
        reviews: "M4 3h16v18H4z M8 8h8 M8 12h8 M8 16h5",
        folder: "M3 5h7l2 3h9v12H3z",
        search: "M17 10a7 7 0 1 1-14 0 7 7 0 1 1 14 0 M15 15l6 6",
        plus: "M12 4v16 M4 12h16",
        close: "M6 6l12 12 M6 18L18 6",
        settings: "M3 6h18 M3 12h18 M3 18h18 M8 3v6 M16 9v6 M10 15v6",
        filter: "M3 5h18 M6 12h12 M9 19h6",
        edit: "M14 5l5 5 M4 20l5-1L21 7l-5-5L4 14z",
        arrow: "M6 9l6 6 6-6",
        image: "M3 3h18v18H3z M3 17l6-6 5 5 3-3 4 4 M14 7h2",
        trash: "M3 6h18 M9 6V3h6v3 M5 6l1 15h12l1-15 M10 10v7 M14 10v7",
        check: "M4 12l5 5L20 6"
    })
    implicitWidth: 22
    implicitHeight: 22
    layer.enabled: true
    layer.samples: 4
    Shape {
        width: 24
        height: 24
        preferredRendererType: Shape.CurveRenderer
        transform: Scale { xScale: root.width / 24; yScale: root.height / 24 }
        ShapePath {
            strokeColor: root.ink
            strokeWidth: 1.6
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: root.paths[root.name] || root.paths.library }
        }
    }
}
