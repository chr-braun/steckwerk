import Foundation

/// Blattgeometrie aus dem SVG der Engine. Steckwerk schreibt nur `<path d="M… L… Z">` mit absoluten
/// Koordinaten in mm (viewBox = Blatt), die Farbe steht am Pfad (`stroke`) oder an der Ebene (`<g>`).
public struct SheetDrawing: Sendable {
    public struct Path: Sendable, Hashable {
        public var subpaths: [[Pt]]
        public var closed: [Bool]
        public var stroke: String
        public var fill: String?
    }

    public var width: Double
    public var height: Double
    public var paths: [Path]

    public init(svg: String, width: Double = 0, height: Double = 0) {
        var w = width, h = height
        if (w <= 0 || h <= 0), let vb = SheetDrawing.viewBox(in: svg) {
            w = vb.0
            h = vb.1
        }
        self.width = w
        self.height = h
        self.paths = SheetDrawing.parsePaths(svg)
    }

    /// Kleinstes Rechteck um alle Punkte (für „Einpassen“).
    public var bounds: (minX: Double, minY: Double, maxX: Double, maxY: Double)? {
        var lo = Pt(.infinity, .infinity), hi = Pt(-.infinity, -.infinity)
        for p in paths { for sp in p.subpaths { for q in sp {
            lo = Pt(min(lo.x, q.x), min(lo.y, q.y))
            hi = Pt(max(hi.x, q.x), max(hi.y, q.y))
        } } }
        return lo.x.isFinite ? (lo.x, lo.y, hi.x, hi.y) : nil
    }

    /// Ist das eine Gravur-Farbe (alles außer der Schnittfarbe)?
    public static func isCut(_ stroke: String, cutColor: String = "#000000") -> Bool {
        let s = stroke.lowercased()
        let c = cutColor.lowercased()
        return s == c || s == "black" || s == "#000" || (c == "#000000" && s == "#000000")
    }

    // MARK: - Parser

    static func viewBox(in svg: String) -> (Double, Double)? {
        guard let v = attribute("viewBox", in: tagSlice(svg, name: "svg") ?? "") else { return nil }
        let n = numbers(v)
        return n.count == 4 ? (n[2], n[3]) : nil
    }

    static func tagSlice(_ svg: String, name: String) -> String? {
        guard let r = svg.range(of: "<\(name)") else { return nil }
        guard let end = svg[r.upperBound...].firstIndex(of: ">") else { return nil }
        return String(svg[r.lowerBound...end])
    }

    /// Alle Pfade; Ebenenfarben aus offenen `<g stroke=…>` werden vererbt.
    static func parsePaths(_ svg: String) -> [Path] {
        var out: [Path] = []
        var strokeStack: [String?] = []
        var fillStack: [String?] = []
        var i = svg.startIndex
        while let lt = svg[i...].firstIndex(of: "<") {
            guard let gt = svg[lt...].firstIndex(of: ">") else { break }
            let tag = svg[svg.index(after: lt)..<gt]
            i = svg.index(after: gt)
            if tag.hasPrefix("/g") {
                if !strokeStack.isEmpty { strokeStack.removeLast(); fillStack.removeLast() }
            } else if tag.hasPrefix("g") && (tag.count == 1 || tag.dropFirst().first?.isWhitespace == true) {
                let selfClosing = tag.hasSuffix("/")
                if !selfClosing {
                    strokeStack.append(attribute("stroke", in: tag))
                    fillStack.append(attribute("fill", in: tag))
                }
            } else if tag.hasPrefix("path") {
                guard let d = attribute("d", in: tag) else { continue }
                let stroke = attribute("stroke", in: tag) ?? strokeStack.last(where: { $0 != nil }) ?? nil
                var fill = attribute("fill", in: tag) ?? fillStack.last(where: { $0 != nil }) ?? nil
                if fill?.lowercased() == "none" { fill = nil }
                let (subs, closed) = parseD(d)
                if !subs.isEmpty {
                    out.append(Path(subpaths: subs, closed: closed, stroke: stroke ?? "#000000", fill: fill))
                }
            }
        }
        return out
    }

    /// Pfaddaten mit M/L/H/V/Z (absolut und relativ). Kurven kommen in Steckwerk-SVGs nicht vor.
    public static func parseD(_ d: String) -> ([[Pt]], [Bool]) {
        var subs: [[Pt]] = []
        var closed: [Bool] = []
        var cur: [Pt] = []
        var pos = Pt(0, 0)
        var start = Pt(0, 0)
        var cmd: Character = "M"
        var nums: [Double] = []

        func flush() {
            if cur.count > 1 { subs.append(cur); closed.append(false) }
            cur = []
        }
        func apply(_ c: Character, _ n: [Double]) {
            switch c {
            case "M", "m":
                var k = 0
                while k + 1 < n.count {
                    let p = c == "m" ? Pt(pos.x + n[k], pos.y + n[k + 1]) : Pt(n[k], n[k + 1])
                    if k == 0 { flush(); start = p }
                    cur.append(p)
                    pos = p
                    k += 2
                }
            case "L", "l":
                var k = 0
                while k + 1 < n.count {
                    let p = c == "l" ? Pt(pos.x + n[k], pos.y + n[k + 1]) : Pt(n[k], n[k + 1])
                    if cur.isEmpty { cur.append(pos) }
                    cur.append(p)
                    pos = p
                    k += 2
                }
            case "H", "h":
                for v in n {
                    let p = Pt(c == "h" ? pos.x + v : v, pos.y)
                    if cur.isEmpty { cur.append(pos) }
                    cur.append(p)
                    pos = p
                }
            case "V", "v":
                for v in n {
                    let p = Pt(pos.x, c == "v" ? pos.y + v : v)
                    if cur.isEmpty { cur.append(pos) }
                    cur.append(p)
                    pos = p
                }
            case "Z", "z":
                if cur.count > 1 { subs.append(cur); closed.append(true) }
                cur = []
                pos = start
            default:
                break
            }
        }

        var token = ""
        func endNumber() {
            if !token.isEmpty, let v = Double(token) { nums.append(v) }
            token = ""
        }
        for ch in d {
            if ch.isLetter && ch != "e" && ch != "E" {
                endNumber()
                apply(cmd, nums)
                nums = []
                cmd = ch
                if ch == "Z" || ch == "z" { apply(ch, []); cmd = "Z" }
            } else if ch == "," || ch.isWhitespace {
                endNumber()
            } else if ch == "-" && !token.isEmpty && token.last != "e" && token.last != "E" {
                endNumber()
                token = "-"
            } else {
                token.append(ch)
            }
        }
        endNumber()
        if cmd != "Z" { apply(cmd, nums) }
        flush()
        return (subs, closed)
    }

    static func attribute<S: StringProtocol>(_ name: String, in tag: S) -> String? {
        let t = String(tag)
        for quote in ["\"", "'"] {
            let needle = " \(name)=\(quote)"
            if let r = t.range(of: needle) {
                let rest = t[r.upperBound...]
                if let end = rest.firstIndex(of: Character(quote)) { return String(rest[..<end]) }
            }
        }
        return nil
    }

    static func numbers(_ s: String) -> [Double] {
        s.split(whereSeparator: { $0 == " " || $0 == "," }).compactMap { Double($0) }
    }
}
