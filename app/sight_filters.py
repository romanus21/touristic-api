FILTERS = {
    0: {"name": "Фонтаны", "SQL": "fountain is not null"},
    1: {"name": "Колёса обозрения", "SQL": "attraction = 'big_wheel'"},
    2: {"name": "Музеи", "SQL": "museum is not null or tourism = 'museum'"},
    3: {"name": "Уличное искусство", "SQL": "tourism = 'artwork'"},
    4: {"name": "Галереи", "SQL": "tourism = 'gallery'"},
    5: {"name": "Зоопарки", "SQL": "tourism = 'zoo' or zoo is not null"},
    6: {"name": "Обзорные точки", "SQL": "tourism = 'viewpoint'"},
    7: {
        "name": "Историческое достопримечательности",
        "SQL": "historic is not null",
    },
    8: {
        "name": "Памятники и монументы",
        "SQL": "memorial is not null or monument is not null",
    },
    9: {"name": "Руины", "SQL": "ruins is not null"},
    10: {
        "name": "Архитектура",
        "SQL": "building is not null",
    },
}
