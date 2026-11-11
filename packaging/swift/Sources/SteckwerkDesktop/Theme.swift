import AppKit
import SwiftUI

/// Farben der Oberfläche: Systemfarben und die Akzentfarbe des Macs, dazu Holztöne für die Platte.
enum Theme {
    private static func dynamic(light: NSColor, dark: NSColor) -> Color {
        Color(nsColor: NSColor(name: nil) { appearance in
            appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua ? dark : light
        })
    }

    private static func rgb(_ hex: UInt32) -> NSColor {
        NSColor(srgbRed: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255,
                blue: CGFloat(hex & 0xFF) / 255, alpha: 1)
    }

    /// Hintergrund hinter der Platte (wie die Arbeitsfläche in Vorschau oder Pages).
    static let canvas = dynamic(light: rgb(0xF4F4F6), dark: rgb(0x161618))
    /// Statusleiste unter der Platte.
    static let statusBar = dynamic(light: rgb(0xF8F8F9), dark: rgb(0x1C1C1E))
    /// Papierblatt, auf dem die Platte liegt.
    static let paper = dynamic(light: .white, dark: rgb(0x242426))
    static let card = Color(nsColor: .controlBackgroundColor)
    static let background = Color(nsColor: .windowBackgroundColor)

    /// Restplatte (Holz) und Teile (heller), Gravur blau.
    static let ply = dynamic(light: rgb(0xE3C792), dark: rgb(0xB39566))
    static let plyEdge = dynamic(light: rgb(0xC9A66B), dark: rgb(0x8D6F45))
    static let part = dynamic(light: rgb(0xF3E2BF), dark: rgb(0xD9C296))
    static let cutLine = dynamic(light: rgb(0x6B4F2A), dark: rgb(0x3A2A14))
    static let engrave = dynamic(light: rgb(0x2B52D9), dark: rgb(0x3D63E6))
    /// Teilenummern-Chip im Prüfbericht.
    static let chip = dynamic(light: rgb(0xF1E2C2), dark: rgb(0x5A4728))
    static let chipInk = dynamic(light: rgb(0x7A5A2C), dark: rgb(0xF0DCB4))

    static let accent = Color.accentColor
    static let cut = Color.primary
    static let ok = dynamic(light: rgb(0x1F8A3A), dark: rgb(0x32D74B))
    static let error = Color(nsColor: .systemRed)
    static let warning = Color(nsColor: .systemOrange)

    static let spacing: CGFloat = 12
    static let cornerRadius: CGFloat = 9
}

struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(Theme.spacing)
            .background(Theme.card, in: RoundedRectangle(cornerRadius: Theme.cornerRadius))
            .overlay(RoundedRectangle(cornerRadius: Theme.cornerRadius).stroke(Color.primary.opacity(0.08)))
    }
}

extension View {
    func card() -> some View { modifier(CardStyle()) }
}

/// Teilenummer als kleines Holz-Etikett, wie sie auch eingraviert wird.
struct PartNumber: View {
    let nr: Int

    var body: some View {
        Text("\(nr)")
            .font(.caption.weight(.semibold))
            .monospacedDigit()
            .foregroundStyle(Theme.chipInk)
            .padding(.horizontal, 5)
            .frame(minWidth: 20, minHeight: 18)
            .background(Theme.chip, in: RoundedRectangle(cornerRadius: 5))
    }
}

/// SF-Symbol für eine Modellgruppe in der Seitenleiste.
enum GroupSymbol {
    static func name(for group: String) -> String {
        switch group {
        case "Häuser": return "house"
        case "Zubehör": return "tree"
        case "Schmuck": return "star"
        case "Fahrzeuge": return "car"
        case "Eigene Motive": return "photo"
        case "Komplett": return "square.grid.2x2"
        case "Wichtel": return "figure.stand"
        case "Halloween": return "moon.stars"
        case "Weihnachten": return "snowflake"
        case "Spiele": return "die.face.5"
        case "Bewegung": return "figure.wave"
        case "Wohnen": return "sofa"
        case "Mehrlagig": return "square.3.layers.3d"
        case "Grundlagen": return "ruler"
        case "Formen": return "square.on.circle"
        case "Verkauf": return "tag"
        default: return "shippingbox"
        }
    }
}
