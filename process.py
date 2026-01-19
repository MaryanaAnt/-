import pandas as pd

def load_sales_data(file_path):
    REQUIRED_COLS = [
        "ID операции",
        "Дата",
        "Адрес магазина",
        "Район магазина",
        "Артикул",
        "Название товара",
        "Отдел товара",
        "Количество упаковок",  # Исправлено: было "Количество упаковок, шт."
        "Тип операции (продажа/поступление)",  # Исправлено: было "Операция"
        "Стоимость одной единицы"  # Исправлено: было "Цена руб./шт."
    ]
    try:
        data = pd.read_csv(file_path, sep=";", encoding="utf-8")
    except Exception:
        try:
            data = pd.read_csv(file_path, sep=";", encoding="cp1251")
        except Exception:
            print(f"Не удалось прочесть файл, проверьте кодировку и разделитель: {file_path}")
            return None

    missing = [col for col in REQUIRED_COLS if col not in data.columns]
    if missing:
        print(f"Не удалось прочесть файл: {file_path}. Отсутствуют обязательные столбцы: {', '.join(missing)}")
        return None

    return data


def preprocess_data(data):
    if data is None:
        return None

    data_clean = data.copy()

    # Преобразование даты
    data_clean["Дата"] = pd.to_datetime(data_clean["Дата"], errors="coerce", dayfirst=True)

    # Количество упаковок → числовой тип
    data_clean["Количество упаковок"] = pd.to_numeric(data_clean["Количество упаковок"], errors="coerce")

    # Стоимость: заменяем запятые на точки
    data_clean["Стоимость одной единицы"] = (
        data_clean["Стоимость одной единицы"].astype(str).str.replace(",", ".", regex=False)
    )
    data_clean["Стоимость одной единицы"] = pd.to_numeric(data_clean["Стоимость одной единицы"], errors="coerce")

    # Удаление строк с пропусками
    before = len(data_clean)
    data_clean = data_clean.dropna()
    removed = before - len(data_clean)
    if removed > 0:
        print(f"Удалено строк с пустыми значениями: {removed}")

    # Создание столбца "Сумма операции"
    data_clean["Сумма операции"] = (
        data_clean["Количество упаковок"] * data_clean["Стоимость одной единицы"]
    )

    return data_clean


def get_operational_data(data_clean, operation_type=None):
    if operation_type is None:
        return data_clean.copy()

    # Приводим к нижнему регистру для сравнения
    operation_type_lower = operation_type.lower().strip()
    filtered_data = data_clean[
        data_clean["Тип операции (продажа/поступление)"].str.lower().str.strip() == operation_type_lower
    ].copy()
    return filtered_data


def calculate_revenue_by_period(data_clean, period='D'):
    sales_data = get_operational_data(data_clean, operation_type="продажа")
    if sales_data.empty:
        print("Нет данных о продажах для расчета выручки.")
        return pd.DataFrame(columns=['Дата', 'Выручка по периоду'])

    if period == 'W':
        revenue_by_period = sales_data.groupby(pd.Grouper(key='Дата', freq='W-MON'))['Сумма операции'].sum().reset_index()
    else:
        revenue_by_period = sales_data.groupby(pd.Grouper(key='Дата', freq=period))['Сумма операции'].sum().reset_index()

    revenue_by_period.columns = ['Дата', 'Выручка по периоду']
    revenue_by_period = revenue_by_period.sort_values('Дата').reset_index(drop=True)
    return revenue_by_period


def calculate_profit_by_period(data_clean, period='D'):
    # Доходы от продаж
    sales_data = get_operational_data(data_clean, "продажа")
    if sales_data.empty:
        print("Нет данных о продажах для расчета прибыли.")
        return None

    # Расходы: поступления
    expense_data = get_operational_data(data_clean, "поступление")

    # Группировка доходов
    if period == 'W':
        income_by_period = sales_data.groupby(pd.Grouper(key='Дата', freq='W-MON'))['Сумма операции'].sum()
    else:
        income_by_period = sales_data.groupby(pd.Grouper(key='Дата', freq=period))['Сумма операции'].sum()

    # Группировка расходов
    if not expense_data.empty:
        if period == 'W':
            expense_by_period = expense_data.groupby(pd.Grouper(key='Дата', freq='W-MON'))['Сумма операции'].sum()
        else:
            expense_by_period = expense_data.groupby(pd.Grouper(key='Дата', freq=period))['Сумма операции'].sum()
    else:
        expense_by_period = pd.Series(0, index=income_by_period.index)

    # Объединяем и считаем прибыль
    profit_data = pd.DataFrame({
        'Доходы': income_by_period,
        'Расходы': expense_by_period.reindex(income_by_period.index, fill_value=0)
    }).fillna(0)

    profit_data['Прибыль по периоду'] = profit_data['Доходы'] - profit_data['Расходы']
    profit_result = profit_data[['Прибыль по периоду']].reset_index()
    profit_result.columns = ['Дата', 'Прибыль по периоду']
    profit_result = profit_result.sort_values('Дата').reset_index(drop=True)

    return profit_result


def aggregate_sales_by_category(data_clean):
    sales_data = get_operational_data(data_clean, "продажа")
    if sales_data.empty:
        return pd.DataFrame()

    agg_dict = {}
    if 'Сумма операции' in sales_data.columns:
        agg_dict['Выручка'] = ('Сумма операции', 'sum')
    if 'Количество упаковок' in sales_data.columns:
        agg_dict['Проданных единиц'] = ('Количество упаковок', 'sum')
    if 'Артикул' in sales_data.columns:
        agg_dict['Уникальных товаров'] = ('Артикул', 'nunique')

    sales_by_category = sales_data.groupby('Отдел товара').agg(**agg_dict)
    category_stats = sales_by_category.sort_index()
    return category_stats


def get_top_n_products(data_clean, n=5, metric='quantity', date='all'):
    sales_data = get_operational_data(data_clean, "продажа")

    if date != 'all':
        try:
            date = pd.to_datetime(date)
            sales_data = sales_data[sales_data["Дата"] == date]
        except:
            print("Некорректная дата. Используется весь период.")
            date = 'all'

    if metric == 'quantity':
        agg_col = 'Количество упаковок'
        result_col = 'Сумма_Количество упаковок'
        agg_func = 'sum'
    elif metric == 'revenue':
        agg_col = 'Сумма операции'
        result_col = 'Сумма_Сумма операции'
        agg_func = 'sum'
    else:
        return None

    grouped_data = sales_data.groupby('Название товара', as_index=False).agg({agg_col: agg_func})
    grouped_data = grouped_data.rename(columns={agg_col: result_col})
    data_sorted = grouped_data.sort_values(by=result_col, ascending=False)
    return data_sorted.head(n).reset_index(drop=True)


def analyze_inventory_turnover(data_clean, top_n=10):
    sales_data = get_operational_data(data_clean, "продажа")
    purchases_data = get_operational_data(data_clean, "поступление")

    # Продажи
    sales_grouped = sales_data.groupby(['Артикул', 'Название товара']).agg({
        'Количество упаковок': 'sum',
        'Сумма операции': 'sum'
    }).reset_index()
    sales_grouped = sales_grouped.rename(columns={
        'Количество упаковок': 'Продано_упаковок',
        'Сумма операции': 'Выручка_от_продаж'
    })

    # Поступления
    purchases_grouped = purchases_data.groupby(['Артикул', 'Название товара']).agg({
        'Количество упаковок': 'sum',
        'Сумма операции': 'sum'
    }).reset_index()
    purchases_grouped = purchases_grouped.rename(columns={
        'Количество упаковок': 'Поступлено_упаковок',
        'Сумма операции': 'Затраты_на_закупки'
    })

    # Объединение
    inventory_analysis = pd.merge(
        sales_grouped, purchases_grouped,
        on=['Артикул', 'Название товара'],
        how='outer'
    ).fillna(0)

    inventory_analysis['Разница_упаковок'] = (
        inventory_analysis['Продано_упаковок'] - inventory_analysis['Поступлено_упаковок']
    )
    inventory_analysis['Прибыль'] = (
        inventory_analysis['Выручка_от_продаж'] - inventory_analysis['Затраты_на_закупки']
    )

    # Рентабельность (избегаем деления на ноль)
    mask = inventory_analysis['Затраты_на_закупки'] > 0
    inventory_analysis['Рентабельность_%'] = 0
    inventory_analysis.loc[mask, 'Рентабельность_%'] = (
        (inventory_analysis.loc[mask, 'Прибыль'] / inventory_analysis.loc[mask, 'Затраты_на_закупки']) * 100
    )

    # Форматирование
    num_cols = ['Продано_упаковок', 'Поступлено_упаковок', 'Разница_упаковок']
    for col in num_cols:
        inventory_analysis[col] = inventory_analysis[col].astype(int)

    money_cols = ['Выручка_от_продаж', 'Затраты_на_закупки', 'Прибыль']
    for col in money_cols:
        inventory_analysis[col] = inventory_analysis[col].round(2)

    inventory_analysis['Рентабельность_%'] = inventory_analysis['Рентабельность_%'].round(2)

    # Сортировка по абсолютной разнице
    inventory_analysis['Абс_разница'] = inventory_analysis['Разница_упаковок'].abs()
    inventory_analysis = inventory_analysis.sort_values('Абс_разница', ascending=False)
    inventory_analysis = inventory_analysis.drop('Абс_разница', axis=1)

    return inventory_analysis.head(top_n).reset_index(drop=True)


def get_inventory_insights(inventory_analysis):
    insights = {
        'overstock_candidates': [],
        'understock_candidates': [],
        'most_profitable': [],
        'least_profitable': [],
        'summary_stats': {}
    }

    if inventory_analysis.empty:
        return insights

    # Дефицит: продажи > поступлений (разница > средней)
    mean_sales = inventory_analysis['Продано_упаковок'].mean()
    overstock_threshold = mean_sales * 0.3
    overstock_items = inventory_analysis[inventory_analysis['Разница_упаковок'] > overstock_threshold]

    # Излишек: поступления > продаж
    understock_threshold = -mean_sales * 0.3
    understock_items = inventory_analysis[inventory_analysis['Разница_упаковок'] < understock_threshold]

    # Топ прибыльных и убыточных
    most_profitable = inventory_analysis.nlargest(5, 'Прибыль')
    least_profitable = inventory_analysis.nsmallest(5, 'Прибыль')

    # Заполнение insights
    insights['overstock_candidates'] = overstock_items[[
        'Артикул', 'Название товара', 'Продано_упаковок', 'Поступлено_упаковок', 'Разница_упаковок'
    ]].to_dict('records')

    insights['understock_candidates'] = understock_items[[
        'Артикул', 'Название товара', 'Продано_упаковок', 'Поступлено_упаковок', 'Разница_упаковок'
    ]].to_dict('records')

    insights['most_profitable'] = most_profitable[[
        'Артикул', 'Название товара', 'Прибыль', 'Рентабельность_%', 'Выручка_от_продаж', 'Затраты_на_закупки'
    ]].to_dict('records')

    insights['least_profitable'] = least_profitable[[
        'Артикул', 'Название товара', 'Прибыль', 'Рентабельность_%', 'Выручка_от_продаж', 'Затраты_на_закупки'
    ]].to_dict('records')

    # Сводная статистика
    insights['summary_stats'] = {
        'total_items': len(inventory_analysis),
        'total_revenue': inventory_analysis['Выручка_от_продаж'].sum(),
        'total_costs': inventory_analysis['Затраты_на_закупки'].sum(),
        'total_profit': inventory_analysis['Прибыль'].sum(),
        'avg_profitability': inventory_analysis['Рентабельность_%'].mean(),
        'items_with_deficit': len(overstock_items),
        'items_with_excess': len(understock_items)
    }

    return insights
