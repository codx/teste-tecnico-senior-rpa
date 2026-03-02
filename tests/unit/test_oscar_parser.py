from bs4 import BeautifulSoup


def parse_oscar_row(year, film_element):
    """
    Simulação da lógica interna de parsing do OscarScraper
    (Extraído do OscarScraper.scrape no app/scrapers/oscar_scraper.py)
    """
    title = film_element.find(class_="film-title").text.strip()
    nominations_text = film_element.find(class_="film-nominations").text.strip()
    awards_text = film_element.find(class_="film-awards").text.strip()

    best_picture = False
    if film_element.find(class_="glyphicon-flag"):
        best_picture = True

    try:
        nominations = int(nominations_text)
    except (ValueError, TypeError):
        nominations = 0

    try:
        awards = int(awards_text)
    except (ValueError, TypeError):
        awards = 0

    try:
        year_int = int(year)
    except (ValueError, TypeError):
        year_int = 0

    return {
        "year": year_int,
        "title": title,
        "nominations": nominations,
        "awards": awards,
        "best_picture": best_picture,
    }


def test_oscar_parser_logic():
    html = """
    <tr class="film">
        <td class="film-title">The King's Speech</td>
        <td class="film-nominations">12</td>
        <td class="film-awards">4</td>
        <td class="film-best-picture">
            <i class="glyphicon glyphicon-flag"></i>
        </td>
    </tr>
    """
    soup = BeautifulSoup(html, "html.parser")
    film_element = soup.find(class_="film")

    data = parse_oscar_row(2010, film_element)

    assert data["title"] == "The King's Speech"
    assert data["year"] == 2010
    assert data["nominations"] == 12
    assert data["awards"] == 4
    assert data["best_picture"] is True


def test_oscar_parser_logic_no_best_picture():
    html = """
    <tr class="film">
        <td class="film-title">Inception</td>
        <td class="film-nominations">8</td>
        <td class="film-awards">4</td>
        <td class="film-best-picture"></td>
    </tr>
    """
    soup = BeautifulSoup(html, "html.parser")
    film_element = soup.find(class_="film")

    data = parse_oscar_row(2010, film_element)

    assert data["title"] == "Inception"
    assert data["best_picture"] is False


def test_oscar_parser_logic_empty_values():
    html = """
    <tr class="film">
        <td class="film-title">Empty Data</td>
        <td class="film-nominations"></td>
        <td class="film-awards"></td>
        <td class="film-best-picture"></td>
    </tr>
    """
    soup = BeautifulSoup(html, "html.parser")
    film_element = soup.find(class_="film")

    data = parse_oscar_row("", film_element)

    assert data["title"] == "Empty Data"
    assert data["year"] == 0
    assert data["nominations"] == 0
    assert data["awards"] == 0
    assert data["best_picture"] is False
