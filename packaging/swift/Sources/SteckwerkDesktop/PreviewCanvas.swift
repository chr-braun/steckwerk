import SteckwerkCore
import SwiftUI

/// Native Blattvorschau: Schnitt schwarz, Gravur blau, Blattrahmen; Zoom per Pinch/Scroll, Ziehen verschiebt.
struct PreviewCanvas: View {
    let drawing: SheetDrawing
    var cutColor = "#000000"
    var checked = true

    @State private var zoom: CGFloat = 1
    @State private var baseZoom: CGFloat = 1
    @State private var offset: CGSize = .zero
    @State private var baseOffset: CGSize = .zero

    var body: some View {
        GeometryReader { geo in
            Canvas { ctx, size in
                draw(in: &ctx, size: size)
            }
            .contentShape(Rectangle())
            .gesture(
                MagnifyGesture()
                    .onChanged { zoom = max(0.2, min(20, baseZoom * $0.magnification)) }
                    .onEnded { _ in baseZoom = zoom }
                    .simultaneously(with: DragGesture()
                        .onChanged { v in
                            offset = CGSize(width: baseOffset.width + v.translation.width,
                                            height: baseOffset.height + v.translation.height)
                        }
                        .onEnded { _ in baseOffset = offset })
            )
            .onTapGesture(count: 2) { reset() }
            .overlay(alignment: .bottomTrailing) { controls }
            .overlay(alignment: .topLeading) {
                if !checked {
                    Text("Vorschau – nicht geprüft")
                        .font(.caption.weight(.semibold))
                        .padding(6)
                        .background(Theme.fehler.opacity(0.15), in: RoundedRectangle(cornerRadius: 6))
                        .padding(10)
                }
            }
            .frame(width: geo.size.width, height: geo.size.height)
        }
    }

    private var controls: some View {
        HStack(spacing: 4) {
            Button { setZoom(zoom / 1.25) } label: { Image(systemName: "minus.magnifyingglass") }
            Text("\(Int(zoom * 100)) %").font(.caption.monospacedDigit()).frame(width: 46)
            Button { setZoom(zoom * 1.25) } label: { Image(systemName: "plus.magnifyingglass") }
            Button { reset() } label: { Image(systemName: "arrow.up.left.and.down.right.magnifyingglass") }
                .help("Einpassen (Doppelklick)")
        }
        .buttonStyle(.borderless)
        .padding(6)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
        .padding(10)
    }

    private func setZoom(_ z: CGFloat) {
        zoom = max(0.2, min(20, z))
        baseZoom = zoom
    }

    private func reset() {
        zoom = 1; baseZoom = 1
        offset = .zero; baseOffset = .zero
    }

    private func draw(in ctx: inout GraphicsContext, size: CGSize) {
        let w = drawing.width > 0 ? drawing.width : 400
        let h = drawing.height > 0 ? drawing.height : 300
        let margin: CGFloat = 24
        let fit = min((size.width - 2 * margin) / w, (size.height - 2 * margin) / h)
        let s = max(fit, 0.01) * zoom
        let ox = (size.width - w * s) / 2 + offset.width
        let oy = (size.height - h * s) / 2 + offset.height
        func pt(_ p: Pt) -> CGPoint { CGPoint(x: ox + p.x * s, y: oy + p.y * s) }

        let sheetRect = CGRect(x: ox, y: oy, width: w * s, height: h * s)
        ctx.fill(Path(sheetRect), with: .color(Theme.sheet))
        ctx.stroke(Path(sheetRect), with: .color(.secondary.opacity(0.6)), style: StrokeStyle(lineWidth: 1, dash: [5, 4]))

        let line = max(0.8, min(2, s * 0.25))
        for p in drawing.paths {
            var path = Path()
            for (i, sub) in p.subpaths.enumerated() {
                path.addLines(sub.map(pt))
                if p.closed.indices.contains(i), p.closed[i] { path.closeSubpath() }
            }
            let cut = SheetDrawing.isCut(p.stroke, cutColor: cutColor)
            if let fill = p.fill, !fill.isEmpty {
                ctx.fill(path, with: .color(Theme.engrave.opacity(0.35)), style: FillStyle(eoFill: true))
            }
            ctx.stroke(path, with: .color(cut ? Theme.cut : Theme.engrave), lineWidth: cut ? line : line * 0.7)
        }
    }
}
