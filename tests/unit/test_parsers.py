from bs4 import BeautifulSoup


def test_hockey_parser_logic():
    html = """
    <table>
        <tr class="team">
            <td class="name">Boston Bruins</td>
            <td class="year">1990</td>
            <td class="wins">44</td>
            <td class="losses">24</td>
            <td class="ot-losses"></td>
            <td class="pct">0.55</td>
            <td class="gf">299</td>
            <td class="ga">264</td>
            <td class="diff">35</td>
        </tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr", class_="team")
    cols = row.find_all("td")

    data = {
        "team_name": cols[0].text.strip(),
        "year": int(cols[1].text.strip()),
        "wins": int(cols[2].text.strip()),
        "losses": int(cols[3].text.strip()),
        "ot_losses": int(cols[4].text.strip()) if cols[4].text.strip() else 0,
        "win_pct": float(cols[5].text.strip()),
        "goals_for": int(cols[6].text.strip()),
        "goals_against": int(cols[7].text.strip()),
        "goal_diff": int(cols[8].text.strip()),
    }

    assert data["team_name"] == "Boston Bruins"
    assert data["year"] == 1990
    assert data["wins"] == 44
    assert data["ot_losses"] == 0
