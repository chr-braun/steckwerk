import SwiftUI

/// Warme Farben passend zur Vorschau der Weboberfläche; im Dunkelmodus Systemfarben.
enum Theme {
    static let accent = Color(red: 0xb4 / 255, green: 0x53 / 255, blue: 0x09 / 255)       // Bernstein #b45309
    static let paper = Color(nsColor: NSColor(name: nil) { appearance in
        appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
            ? NSColor(white: 0.16, alpha: 1)
            : NSColor(red: 0xf5 / 255, green: 0xf2 / 255, blue: 0xec / 255, alpha: 1)      // #f5f2ec
    })
    static let sheet = Color(nsColor: NSColor(name: nil) { appearance in
        appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
            ? NSColor(white: 0.22, alpha: 1) : .white
    })
    static let ok = Color.green
    static let warnung = Color.orange
    static let fehler = Color.red
    static let cut = Color.primary
    static let engrave = Color.blue

    static let padding: CGFloat = 16
    static let corner: CGFloat = 10
}

struct Card<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(Theme.padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.sheet, in: RoundedRectangle(cornerRadius: Theme.corner))
            .overlay(RoundedRectangle(cornerRadius: Theme.corner).strokeBorder(.separator))
    }
}
