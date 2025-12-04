import io
import math
import requests
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageOps, ImageFilter

IMG_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/Rainbow_lorikeet_%28Trichoglossus_moluccanus_moluccanus%29_Sydney.jpg/500px-Rainbow_lorikeet_%28Trichoglossus_moluccanus_moluccanus%29_Sydney.jpg"

def fetch_remote_image(url: str, timeout: int = 20) -> Image.Image:
    """
    Pobiera obraz zdalny i sprawdza podstawowe warunki:
    - status 200
    - nagłówek Content-Type wskazuje na obraz
    Zwraca obiekt PIL.Image.
    """
    headers = {
        "User-Agent": "Python-Image-Quality-Analyzer/1.0"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Nieudany odczyt: HTTP {resp.status_code}")

    ctype = resp.headers.get("Content-Type", "").lower()
    if not any(fmt in ctype for fmt in ["image/jpeg", "image/png", "image/webp"]):
        raise RuntimeError(f"Nieobsługiwany Content-Type: {ctype}")

    # Dodatkowo: sprawdzenie rozmiaru
    if len(resp.content) < 1024:
        raise RuntimeError("Plik wydaje się zbyt mały lub uszkodzony.")

    img = Image.open(io.BytesIO(resp.content))
    # Upewnij się, że to RGB
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    elif img.mode == "RGBA":
        img = img.convert("RGB")
    return img

def compute_histograms(img: Image.Image):
    """
    Zwraca histogramy:
    - kanały R, G, B (tablice 256-elementowe)
    - luma (Y) w przestrzeni prostego przekształcenia: Y = 0.2126 R + 0.7152 G + 0.0722 B
    """
    arr = np.asarray(img, dtype=np.uint8)
    if arr.ndim == 2:  # obraz w skali szarości
        gray = arr
        hist_luma, _ = np.histogram(gray, bins=256, range=(0, 255))
        # Dla spójności tworzymy też RGB skopiowane ze skali szarości
        hist_r = hist_g = hist_b = hist_luma.copy()
    else:
        r = arr[:, :, 0].astype(np.uint8)
        g = arr[:, :, 1].astype(np.uint8)
        b = arr[:, :, 2].astype(np.uint8)
        hist_r, _ = np.histogram(r, bins=256, range=(0, 255))
        hist_g, _ = np.histogram(g, bins=256, range=(0, 255))
        hist_b, _ = np.histogram(b, bins=256, range=(0, 255))
        # Luma z współczynnikami Rec.709
        luma = (0.2126 * r + 0.7152 * g + 0.0722 * b).astype(np.uint8)
        hist_luma, _ = np.histogram(luma, bins=256, range=(0, 255))
    return hist_r, hist_g, hist_b, hist_luma

def histogram_metrics(hist: np.ndarray, total_pixels: int, edge_bins: int = 2):
    """
    Oblicza metryki jakości na podstawie histogramu:
    - clipping_shadows: udział pikseli w najniższych koszach (0..edge_bins-1)
    - clipping_highlights: udział pikseli w najwyższych koszach (255-edge_bins..255)
    - dynamic_range_bins: liczba koszy z niezerową wartością
    - mean_level: średni poziom jasności (ważony histogramem)
    - std_level: odchylenie standardowe poziomu (kontrast)
    """
    bins = np.arange(256)
    total = max(total_pixels, 1)
    # Clipping na krawędziach
    clip_lo = hist[:edge_bins].sum() / total
    clip_hi = hist[-edge_bins:].sum() / total
    # Zakres tonalny (ile koszy niezerowych)
    dr_bins = np.count_nonzero(hist)
    # Średnia i odchylenie standardowe
    mean = (hist * bins).sum() / total
    var = (hist * (bins - mean) ** 2).sum() / total
    std = math.sqrt(var)
    return {
        "clipping_shadows": float(clip_lo),
        "clipping_highlights": float(clip_hi),
        "dynamic_range_bins": int(dr_bins),
        "mean_level": float(mean),
        "std_level": float(std),
    }

def color_balance_metrics(hist_r, hist_g, hist_b, total_pixels: int):
    """
    Ocena balansu kolorów: porównanie średnich kanałów.
    Zwraca różnice między średnimi kanałów oraz wskaźnik odchyłki (im większy, tym gorsza równowaga).
    """
    bins = np.arange(256)
    mean_r = (hist_r * bins).sum() / total_pixels
    mean_g = (hist_g * bins).sum() / total_pixels
    mean_b = (hist_b * bins).sum() / total_pixels
    mean_rgb = np.array([mean_r, mean_g, mean_b])
    center = mean_rgb.mean()
    # Suma bezwzględnych odchyleń od środka (prosty wskaźnik dominanty barwowej)
    color_cast_index = float(np.abs(mean_rgb - center).sum())
    return {
        "mean_r": float(mean_r),
        "mean_g": float(mean_g),
        "mean_b": float(mean_b),
        "color_cast_index": color_cast_index
    }

def assess_quality(img: Image.Image, hist_r, hist_g, hist_b, hist_luma):
    """
    Łączy metryki w ocenę jakości.
    Zwraca werdykt i szczegółowe metryki.
    Kryteria (przykładowe, praktyczne):
    - clipping_shadows/highlights > 0.01 → potencjalne przepalenia/zalanie cieni
    - dynamic_range_bins < 180 → niski zakres tonalny (mało kontrastu / zbyt wąski histogram)
    - std_level_luma < 40 → niski kontrast
    - color_cast_index > 10 → wyraźna dominanta kolorystyczna (balans bieli)
    """
    arr = np.asarray(img)
    total_pixels = arr.shape[0] * arr.shape[1]
    m_r = histogram_metrics(hist_r, total_pixels)
    m_g = histogram_metrics(hist_g, total_pixels)
    m_b = histogram_metrics(hist_b, total_pixels)
    m_l = histogram_metrics(hist_luma, total_pixels)
    m_color = color_balance_metrics(hist_r, hist_g, hist_b, total_pixels)

    issues = []

    # Klipowanie świateł/cieni (na podstawie luma)
    if m_l["clipping_shadows"] > 0.01:
        issues.append(("cienie", m_l["clipping_shadows"]))
    if m_l["clipping_highlights"] > 0.01:
        issues.append(("światła", m_l["clipping_highlights"]))

    # Zakres tonalny
    if m_l["dynamic_range_bins"] < 180:
        issues.append(("zakres_tonalny", m_l["dynamic_range_bins"]))

    # Kontrast
    if m_l["std_level"] < 40:
        issues.append(("kontrast", m_l["std_level"]))

    # Balans kolorów
    if m_color["color_cast_index"] > 10:
        issues.append(("balans_kolorów", m_color["color_cast_index"]))

    verdict = "dobre" if len(issues) == 0 else "wymaga_poprawy"
    metrics = {
        "luma": m_l,
        "r": m_r,
        "g": m_g,
        "b": m_b,
        "color": m_color,
        "issues": issues,
        "verdict": verdict
    }
    return metrics

def improve_image(img: Image.Image, metrics: dict) -> Image.Image:
    """
    Proste, bezpieczne poprawki:
    - Auto-contrast (odrzucenie 1% skrajnych wartości) → lepszy zakres tonalny.
    - Korekcja balansu bieli metodą 'gray-world' (prostolinijna normalizacja kanałów).
    - Delikatna korekcja gamma (np. 0.95–1.05) zależnie od średniej luma.
    - Lekki unsharp mask (wyostrzenie).
    """
    improved = img.copy().convert("RGB")

    # 1) Auto-contrast z odrzuceniem ekstremów
    improved = ImageOps.autocontrast(improved, cutoff=1)

    # 2) Gray-world white balance
    arr = np.asarray(improved).astype(np.float32)
    means = arr.reshape(-1, 3).mean(axis=0)  # [mean_r, mean_g, mean_b]
    target = float(np.mean(means))
    scale = np.where(means > 0, target / means, 1.0)
    arr_bal = np.clip(arr * scale, 0, 255).astype(np.uint8)
    improved = Image.fromarray(arr_bal, mode="RGB")

    # 3) Delikatna korekcja gamma w zależności od jasności
    arr_luma = (0.2126 * arr_bal[:, :, 0] + 0.7152 * arr_bal[:, :, 1] + 0.0722 * arr_bal[:, :, 2])
    mean_luma = float(arr_luma.mean())
    # Jeśli bardzo ciemny → rozjaśnij, jeśli bardzo jasny → przyciemnij
    if mean_luma < 90:
        gamma = 0.9  # rozjaśnienie
    elif mean_luma > 165:
        gamma = 1.1  # przyciemnienie
    else:
        gamma = 1.0
    if abs(gamma - 1.0) > 1e-3:
        # LUT gamma
        def gamma_lut(g):
            x = np.arange(256, dtype=np.float32) / 255.0
            y = np.clip((x ** g) * 255.0, 0, 255).astype(np.uint8)
            return y
        lut = gamma_lut(gamma)
        improved = improved.point(lut * 3)  # dla 3 kanałów

    # 4) Lekki unsharp mask
    improved = improved.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))

    return improved

def plot_histograms(img: Image.Image, hist_r, hist_g, hist_b, hist_luma):
    """
    Rysuje histogramy: RGB oraz luma.
    """
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    bins = np.arange(256)

    axs[0, 0].imshow(img)
    axs[0, 0].set_title("Obraz")
    axs[0, 0].axis("off")

    axs[0, 1].plot(bins, hist_r, color="red", label="R")
    axs[0, 1].plot(bins, hist_g, color="green", label="G")
    axs[0, 1].plot(bins, hist_b, color="blue", label="B")
    axs[0, 1].set_title("Histogram kanałów RGB")
    axs[0, 1].set_xlim(0, 255)
    axs[0, 1].legend()

    axs[1, 0].plot(bins, hist_luma, color="black", label="Luma")
    axs[1, 0].set_title("Histogram luma (Y)")
    axs[1, 0].set_xlim(0, 255)
    axs[1, 0].legend()

    # Histogram łączony (sumaryczny)
    hist_sum = hist_r + hist_g + hist_b
    axs[1, 1].plot(bins, hist_sum, color="gray", label="Suma RGB")
    axs[1, 1].set_title("Histogram sumaryczny (RGB)")
    axs[1, 1].set_xlim(0, 255)
    axs[1, 1].legend()

    plt.tight_layout()
    plt.show()

def print_metrics(metrics: dict):
    """
    Wypisuje metryki i werdykt.
    """
    print("Werdykt jakości:", metrics["verdict"])
    print("\nMetryki luma:")
    for k, v in metrics["luma"].items():
        print(f"  {k}: {v}")
    print("\nBalans kolorów:")
    for k, v in metrics["color"].items():
        print(f"  {k}: {v}")
    if metrics["issues"]:
        print("\nZdiagnozowane problemy:")
        for name, value in metrics["issues"]:
            print(f"  - {name}: {value}")
    else:
        print("\nBrak istotnych problemów wykrytych na podstawie histogramu.")

def main():
    # 1) Pobranie obrazu i weryfikacja podstawowych warunków
    img = fetch_remote_image(IMG_URL)

    # 2) Obliczenia histogramów
    hist_r, hist_g, hist_b, hist_luma = compute_histograms(img)

    # 3) Ocena jakości
    metrics = assess_quality(img, hist_r, hist_g, hist_b, hist_luma)
    print_metrics(metrics)

    # 4) Wizualizacja histogramów
    plot_histograms(img, hist_r, hist_g, hist_b, hist_luma)

    # 5) Poprawa obrazu, jeśli wymaga
    if metrics["verdict"] == "wymaga_poprawy":
        improved = improve_image(img, metrics)
        hist_r2, hist_g2, hist_b2, hist_luma2 = compute_histograms(improved)
        metrics2 = assess_quality(improved, hist_r2, hist_g2, hist_b2, hist_luma2)

        print("\nPo poprawkach:")
        print_metrics(metrics2)
        plot_histograms(improved, hist_r2, hist_g2, hist_b2, hist_luma2)

        # Zapis poprawionego obrazu obok
        improved.save("improved.jpg", quality=92)
        print("\nZapisano plik: improved.jpg")
    else:
        print("\nObraz został oceniony jako dobrej jakości. Nie wykonano korekt.")

if __name__ == "__main__":
    main()
