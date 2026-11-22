import CoreGraphics
import Foundation

let pid = Int(CommandLine.arguments[1])!
let windows = CGWindowListCopyWindowInfo([.optionAll], kCGNullWindowID) as! [[String: Any]]
var best: (area: Double, text: String)? = nil
for window in windows where (window[kCGWindowOwnerPID as String] as? Int) == pid
    && (window[kCGWindowLayer as String] as? Int) == 0 {
    let bounds = window[kCGWindowBounds as String] as! [String: Any]
    let x = bounds["X"] as! Double
    let y = bounds["Y"] as! Double
    let width = bounds["Width"] as! Double
    let height = bounds["Height"] as! Double
    if best == nil || width * height > best!.area {
        best = (width * height, "\(Int(x)); \(Int(y)); \(Int(width)); \(Int(height)); 0")
    }
}
if let found = best {
    print(found.text)
} else {
    exit(1)
}
