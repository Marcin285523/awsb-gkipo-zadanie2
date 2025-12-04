# Analiza i poprawa jakości obrazu

Program do automatycznej oceny jakości obrazów na podstawie analizy histogramów oraz ich inteligentnej poprawy z wykorzystaniem bibliotek PIL, NumPy i Matplotlib.

## Spis treści

- [Opis](#opis)
- [Wymagania](#wymagania)
- [Instalacja](#instalacja)
- [Użycie](#użycie)
- [Funkcjonalności](#funkcjonalności)
- [Metryki jakości](#metryki-jakości)
- [Przykład działania](#przykład-działania)
- [Algorytmy poprawy](#algorytmy-poprawy)
- [Konfiguracja](#konfiguracja)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)
- [Autor](#autor)
- [Licencja](#licencja)

## Opis

Program stanowi zaawansowane narzędzie do analizy jakości obrazów cyfrowych. Pobiera obraz z internetu, analizuje jego histogramy (RGB i luma), diagnozuje potencjalne problemy jakościowe oraz automatycznie aplikuje inteligentne korekty. System ocenia aspekty takie jak:

- Klipowanie świateł i cieni (przepalenia/zalanie)
- Zakres tonalny i kontrast
- Balans bieli i dominanta kolorystyczna
- Dynamikę obrazu

Po wykryciu problemów program automatycznie aplikuje odpowiednie korekty: auto-kontrast, balans bieli metodą gray-world, korekcję gamma oraz wyostrzenie.

## Wymagania

- Python 3.7 lub nowszy
- Połączenie z internetem (do pobierania obrazów)

### Biblioteki

- `Pillow` (PIL) >= 9.0.0
- `numpy` >= 1.21.0
- `matplotlib` >= 3.3.0
- `requests` >= 2.25.0

## Instalacja

1. Sklonuj repozytorium lub pobierz pliki projektu:

```bash
git clone <url-repozytorium>
cd <nazwa-projektu>
```

2. Zainstaluj wymagane biblioteki:

```bash
pip install Pillow numpy matplotlib requests
```

Lub z pliku requirements.txt:

```bash
pip install -r requirements.txt
```

## Użycie

Uruchom program za pomocą interpretera Python:

```bash
python GKiPO_zad2.py
```

Program automatycznie:
1. Pobierze obraz z określonego URL
2. Przeprowadzi weryfikację formatu i poprawności pliku
3. Obliczy histogramy dla kanałów RGB oraz luma (Y)
4. Dokona oceny jakości na podstawie zdefiniowanych metryk
5. Wyświetli szczegółowe metryki w konsoli
6. Pokaże wizualizacje histogramów
7. Jeśli wykryje problemy - automatycznie poprawi obraz
8. Wyświetli histogramy poprawionego obrazu
9. Zapisze poprawiony obraz jako `improved.jpg`

## Funkcjonalności

### 1. Pobieranie i weryfikacja obrazu

Program bezpiecznie pobiera obraz z internetu używając biblioteki `requests` z odpowiednimi nagłówkami User-Agent. Weryfikuje:
- Status odpowiedzi HTTP (200)
- Typ MIME (JPEG, PNG, WebP)
- Minimalny rozmiar pliku (1024 bajty)
- Poprawność struktury obrazu

### 2. Obliczanie histogramów

Program generuje cztery rodzaje histogramów:
- **Kanały RGB**: Osobne histogramy dla czerwieni, zieleni i błękitu
- **Luma (Y)**: Histogram jasności zgodny ze standardem Rec.709
  - Wzór: `Y = 0.2126 × R + 0.7152 × G + 0.0722 × B`

### 3. Analiza metryk jakości

Dla każdego histogramu obliczane są:
- **Clipping shadows**: Procent pikseli w ciemnych obszarach (0-1)
- **Clipping highlights**: Procent pikseli w jasnych obszarach (254-255)
- **Dynamic range bins**: Liczba wykorzystanych poziomów tonalnych (0-256)
- **Mean level**: Średni poziom jasności
- **Standard deviation**: Odchylenie standardowe (miara kontrastu)

### 4. Ocena balansu kolorów

- Porównanie średnich poziomów kanałów RGB
- **Color cast index**: Wskaźnik dominanty kolorystycznej
  - Im wyższa wartość, tym większe zabarwienie

### 5. Inteligentna poprawa obrazu

Program automatycznie aplikuje szereg korekt:

**Auto-kontrast** - Rozciąganie histogramu z odrzuceniem 1% skrajnych wartości
**Balans bieli (Gray World)** - Normalizacja średnich wartości kanałów RGB
**Korekcja gamma** - Dynamiczna korekta zależna od średniej jasności:
  - Luma < 90: γ = 0.9 (rozjaśnienie)
  - Luma > 165: γ = 1.1 (przyciemnienie)
  - Luma 90-165: γ = 1.0 (bez zmian)
**Unsharp Mask** - Delikatne wyostrzenie (radius=1.5, percent=120, threshold=3)

### 6. Wizualizacja wyników

Program generuje dwa zestawy wykresów:
- Oryginalny obraz z histogramami (RGB, luma, sumaryczny)
- Poprawiony obraz z histogramami (jeśli wykonano korekty)

## Metryki jakości

### Kryteria oceny (progi ostrzegawcze)

| Metryka | Próg | Znaczenie |
|---------|------|-----------|
| `clipping_shadows` | > 1% | Zbyt wiele zalanych cieni |
| `clipping_highlights` | > 1% | Zbyt wiele przepalonych świateł |
| `dynamic_range_bins` | < 180 | Wąski zakres tonalny |
| `std_level` (luma) | < 40 | Niski kontrast |
| `color_cast_index` | > 10 | Wyraźna dominanta kolorystyczna |

### Werdykty

- **dobre**: Wszystkie metryki w normie
- **wymaga_poprawy**: Co najmniej jedna metryka przekroczyła próg

## Przykład działania

```
Werdykt jakości: wymaga_poprawy

Metryki luma:
  clipping_shadows: 0.0034
  clipping_highlights: 0.0156
  dynamic_range_bins: 245
  mean_level: 142.3
  std_level: 52.8

Balans kolorów:
  mean_r: 145.2
  mean_g: 138.7
  mean_b: 143.1
  color_cast_index: 8.4

Zdiagnozowane problemy:
  - światła: 0.0156

[Wyświetlenie okna z histogramami]

Po poprawkach:
Werdykt jakości: dobre

[Wyświetlenie okna z poprawionymi histogramami]

Zapisano plik: improved.jpg
```

### Schemat działania programu

```
URL obrazu
    ↓
Pobieranie i weryfikacja (HTTP 200, MIME, rozmiar)
    ↓
Konwersja do RGB
    ↓
Obliczanie histogramów (R, G, B, Luma)
    ↓
Analiza metryk ← Progi jakości
    ↓
Werdykt: dobre / wymaga_poprawy
    ↓
[jeśli wymaga_poprawy]
    ↓
Korekty: auto-kontrast, balans bieli, gamma, wyostrzenie
    ↓
Ponowna analiza metryk
    ↓
Zapis pliku improved.jpg
```

## Algorytmy poprawy

### 1. Auto-kontrast (Histogram Stretching)

Rozciąga histogram odrzucając 1% najciemniejszych i najjaśniejszych pikseli. Poprawia dynamikę obrazu bez wprowadzania artefaktów.

### 2. Gray World White Balance

Zakłada, że średnia sceny powinna być szara (neutralna). Normalizuje średnie wartości każdego kanału RGB:

```
target = mean(mean_R, mean_G, mean_B)
scale_R = target / mean_R
scale_G = target / mean_G
scale_B = target / mean_B
```

### 3. Adaptacyjna korekcja gamma

Dynamicznie dostosowuje gamma w zależności od średniej jasności obrazu. Jasne obrazy są przyciemniane, ciemne rozjaśniane.

### 4. Unsharp Mask

Wyostrza obraz przez odjęcie rozmytej wersji obrazu od oryginału. Parametry są dostosowane aby uniknąć przesady (halos, szumy).

## Konfiguracja

### Zmiana URL obrazu

Edytuj zmienną `IMG_URL` w pliku:

```python
IMG_URL = "https://twoj-url-do-obrazu.jpg"
```

### Dostosowanie progów jakości

W funkcji `assess_quality()` możesz zmienić progi:

```python
if m_l["clipping_shadows"] > 0.01:  # zmień na 0.02 dla mniejszej czułości
if m_l["dynamic_range_bins"] < 180:  # zmień na 150 dla mniejszej czułości
```

### Modyfikacja algorytmów poprawy

W funkcji `improve_image()` możesz dostosować:

```python
# Auto-kontrast: zmień cutoff (domyślnie 1%)
improved = ImageOps.autocontrast(improved, cutoff=2)

# Unsharp Mask: zmień parametry wyostrzenia
improved = improved.filter(ImageFilter.UnsharpMask(
    radius=2.0,    # domyślnie 1.5
    percent=150,   # domyślnie 120
    threshold=5    # domyślnie 3
))
```

## Rozwiązywanie problemów

### Program nie może pobrać obrazu

**Problem**: `RuntimeError: Nieudany odczyt: HTTP 403/404`

**Rozwiązanie**:
- Sprawdź poprawność URL
- Upewnij się, że masz połączenie z internetem
- Niektóre serwery blokują automatyczne requesty - spróbuj innego obrazu

### Błąd: "Nieobsługiwany Content-Type"

**Problem**: Serwer zwraca nieprawidłowy typ MIME

**Rozwiązanie**:
- Upewnij się, że URL wskazuje bezpośrednio na plik obrazu (jpg, png, webp)
- Unikaj linków do stron HTML zawierających obraz

### Matplotlib nie wyświetla wykresów

**Problem**: Okna nie pojawiają się

**Rozwiązanie**:
```python
# Dodaj na początku pliku
import matplotlib
matplotlib.use('TkAgg')  # lub 'Qt5Agg'
```

### "Plik wydaje się zbyt mały lub uszkodzony"

**Problem**: Obraz ma mniej niż 1024 bajty

**Rozwiązanie**:
- Sprawdź czy URL jest poprawny
- Spróbuj pobrać obraz ręcznie w przeglądarce
- Zmień próg w funkcji `fetch_remote_image()`:

```python
if len(resp.content) < 512:  # zmniejsz próg
```

### Korekty pogorszyły obraz

**Problem**: Poprawiony obraz wygląda gorzej niż oryginalny

**Rozwiązanie**:
- Algorytmy są ogólnego przeznaczenia i mogą nie pasować do wszystkich obrazów
- Dostosuj progi w `assess_quality()` lub parametry w `improve_image()`
- Wyłącz wybrane korekty komentując odpowiednie linie

## Rozszerzenia

### Możliwe usprawnienia

1. **Detekcja rozmycia** - analiza gradientów Laplace'a
2. **Detekcja szumu** - ocena wariancji w jednolitych obszarach
3. **Analiza nasycenia kolorów** - sprawdzanie żywości barw
4. **HDR tone mapping** - dla obrazów o wysokiej dynamice
5. **Batch processing** - przetwarzanie wielu obrazów
6. **GUI** - interfejs graficzny do interaktywnej analizy
7. **Eksport raportów** - generowanie PDF z metrykami

## Licencja

Projekt udostępniony na licencji MIT. 

**Uwaga dotycząca obrazów**: Przykładowy obraz papugi tęczowej pochodzi z Wikimedia Commons i jest dostępny na licencji Creative Commons. Zawsze sprawdzaj prawa autorskie do obrazów przed ich wykorzystaniem w projektach komercyjnych.

---

**Uwaga**: Program służy celom edukacyjnym i demonstracyjnym. Automatyczne korekty mogą nie być optymalne dla wszystkich typów obrazów (np. artystyczne zdjęcia z celową dominantą kolorystyczną, obrazy low-key/high-key). Zawsze weryfikuj wyniki wizualnie.
