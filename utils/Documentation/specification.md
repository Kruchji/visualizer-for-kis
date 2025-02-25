## Ordering Visualizer for Known-item search

Aplikace se bude skládat z:

### 1) Frontend

Skládal by se z několika stránek:

**Úvodní stránka** by obsahovala informace o projektu, sbírání dat a navigaci v aplikaci. Dále by obsahovala tlačítko pro spuštění vlastního testu. Mohla by také obsahovat volbu jazyka, popř. volbu tmavého / světlého režimu.

Po kliknutí na tlačítko je uživatel přesměrován do vlastní **stránky s galerií obrázků**. Zde budou do mřížky v určitém uspořádání načteny obrázky – JS uspořádá na základě dat z backendu. V horním menu bude zobrazeno info o postupu a ovládací tlačítka. Pomocí nich půjde zobrazit hledaný obrázek (popř. jej bude možno zobrazit klávesou) a zapnout fullscreen. Uživatel bude moci klikat na obrázky v galerii pro porovnání s targetem a odevzdání. Při špatné volbě může obrázek např. zešednou / zčervenat, při správné JS načte dataset a uspořádání dalšího testu. Pokud bude toto chvíli trvat, může být zobrazen overlay načítání.

Při probíhajícím testu JS pravidelně **sbírá data** o scrollování (např. pomocí `document.documentElement.scrollTop`), velikosti okna / displeje, popř. času, počtu a míst špatných pokusů, již zobrazení hledaného obrázku, porovnání obrázků atd. Data jsou průběžně odesílána na backend, který je bude sbírat a ukládat.

Až uživatel projde všemi testy, tak je přesměrován na stránku s informací o **konci testu** a tlačítku pro zahájení dalšího testu.

Pro frontend tedy bude využito HTML, CSS (s možným použitím knihovny Bootstrap) a JS (s knihovnou jQuery).

### 2) Backend

Backend se bude skládat hlavně z Python serveru a dalších Python skriptů, popř. kolekcí obrázků (datasetů) a konfiguračních souborů.

**Server** bude poskytovat data o uspořádání a konfigurací obrázků frontendu a naopak bude od něj přijímat a ukládat data o scrollování a dalších logovaných událostech (odevzdání). Bude také zodpovědný za vytváření nových uživatelů a jejich konfigurací.

**Data** budou ukládána do txt (v CSV formátu) souborů a konfigurace do JSON souborů. Data o scrollování budou obsahovat User ID, ID iterace, timestamp, odscrollovanný počet pixelů a rozměry okna. Data o interakcích pak budou podobná, ale budou také obsahovat identifikaci nakliklého obrázku a typ interakce. Konfigurace pak budou zahrnovat uspořádání obrázků, volbu targetů a datasetů, postup uživatele, počet načtení stránky a počet sloupců.

Přiloženy budou také **skripty** pro generování grafů ze sesbíraných dat a generování targetů pro jednotlivé datasety. Případně budou použity další skripty pro různá uspořádání obrázků, např. pro self-sorting.