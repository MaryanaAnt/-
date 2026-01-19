import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from process import (
    load_sales_data, preprocess_data, calculate_revenue_by_period,
    calculate_profit_by_period, aggregate_sales_by_category,
    get_top_n_products, analyze_inventory_turnover, get_inventory_insights
)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def save_report_to_file(content, filename="inventory_report.txt"):
    """Сохраняет отчёт в текстовый файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n✅ Отчёт сохранён в файл: {filename}")


def present_revenue_by_period(data, period='D'):
    revenue_data = calculate_revenue_by_period(data, period)

    if revenue_data.empty:
        print("Нет данных для визуализации выручки.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(revenue_data['Дата'], revenue_data['Выручка по периоду'], marker='o', linewidth=2, color='green')
    plt.title(f'Динамика выручки по {("дням" if period=="D" else "неделям" if period=="W" else "месяцам")}', fontsize=16, fontweight='bold')
    plt.xlabel('Дата')
    plt.ylabel('Выручка, руб.')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def visualize_category_analysis(data_clean):
    category_stats = aggregate_sales_by_category(data_clean)
    if category_stats.empty:
        print("Нет данных для визуализации по категориям.")
        return

    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(1, len(category_stats.columns), figsize=(5 * len(category_stats.columns), 6))
    if len(category_stats.columns) == 1:
        axes = [axes]

    colors = sns.color_palette("husl", len(category_stats))

    for i, metric in enumerate(category_stats.columns):
        axes[i].bar(category_stats.index, category_stats[metric], color=colors)
        axes[i].set_title(f'{metric.replace("_", " ").title()} по категориям', fontweight='bold')
        axes[i].set_ylabel(metric)
        axes[i].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.show()


def analyze_real_data(cleaned_data, period):
    profit_data = calculate_profit_by_period(cleaned_data, period)
    if profit_data is None or profit_data.empty:
        print("Не удалось рассчитать прибыль.")
        return

    print("\n" + "="*40)
    print("АНАЛИЗ 1: ПРИБЫЛЬ ПО ПЕРИОДАМ")
    print("="*40)
    print("Прибыль по периодам (первые 10 строк):")
    print(profit_data.head(10))

    # Визуализация
    plt.figure(figsize=(12, 6))
    plt.plot(profit_data['Дата'], profit_data['Прибыль по периоду'], marker='o', linewidth=2, color='blue')
    plt.title('Динамика прибыли по периодам', fontweight='bold')
    plt.xlabel('Дата')
    plt.ylabel('Прибыль, руб.')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    print(f"\nСтатистика прибыли:")
    print(f"Максимальная прибыль: {profit_data['Прибыль по периоду'].max():.2f} руб.")
    print(f"Минимальная прибыль: {profit_data['Прибыль по периоду'].min():.2f} руб.")
    print(f"Средняя прибыль: {profit_data['Прибыль по периоду'].mean():.2f} руб.")
    print(f"Общая прибыль: {profit_data['Прибыль по периоду'].sum():.2f} руб.")


def present_top_n_products(data, n, metric):
    df = get_top_n_products(data, n, metric)
    if df is None or df.empty:
        print("Нет данных для топ-товаров.")
        return

    plt.figure(figsize=(10, 6))
    if metric == 'quantity':
        y_col = 'Сумма_Количество упаковок'
        title = "Топ самых продаваемых товаров по количеству"
    else:
        y_col = 'Сумма_Сумма операции'
        title = "Топ самых продаваемых товаров по выручке"

    # Горизонтальный барплот — НАЗВАНИЯ ТЕПЕРЬ ЧИТАЕМЫ!
    plt.barh(df['Название товара'], df[y_col], edgecolor='black', color='skyblue')
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(y_col.replace("Сумма_", "").replace("_", " ").title())
    plt.ylabel('Название товара')
    plt.gca().invert_yaxis()  # Самые продаваемые — наверху
    plt.tight_layout()
    plt.show()


def print_inventory_report(data, top_n):
    inventory_analysis = analyze_inventory_turnover(data, top_n)
    insights = get_inventory_insights(inventory_analysis)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("АНАЛИЗ ДВИЖЕНИЯ ТОВАРОВ И ИХ РЕНТАБЕЛЬНОСТИ")
    report_lines.append("=" * 80)

    report_lines.append("\nСВОДНАЯ СТАТИСТИКА:")
    report_lines.append("-" * 40)
    stats = insights['summary_stats']
    report_lines.append(f"Всего товаров в анализе: {stats['total_items']}")
    report_lines.append(f"Общая выручка: {stats['total_revenue']:,.2f} руб.")
    report_lines.append(f"Общие затраты на закупки: {stats['total_costs']:,.2f} руб.")
    report_lines.append(f"Общая прибыль: {stats['total_profit']:,.2f} руб.")
    report_lines.append(f"Средняя рентабельность: {stats['avg_profitability']:.2f}%")
    report_lines.append(f"Товаров с возможным дефицитом: {stats['items_with_deficit']}")
    report_lines.append(f"Товаров с возможным излишком: {stats['items_with_excess']}")

    report_lines.append("\nТОВАРЫ С ВОЗМОЖНЫМ ДЕФИЦИТОМ (продажи > поступления):")
    report_lines.append("-" * 40)
    if insights['overstock_candidates']:
        for item in insights['overstock_candidates'][:5]:
            report_lines.append(f"• {item['Название товара']} ({item['Артикул']})")
            report_lines.append(f"  Продано: {item['Продано_упаковок']} уп., Поступило: {item['Поступлено_упаковок']} уп.")
            report_lines.append(f"  Разница: +{item['Разница_упаковок']} уп. (дефицит)")
    else:
        report_lines.append("Нет товаров с явным дефицитом")

    report_lines.append("\nТОВАРЫ С ВОЗМОЖНЫМ ИЗЛИШКОМ (поступления > продаж):")
    report_lines.append("-" * 40)
    if insights['understock_candidates']:
        for item in insights['understock_candidates'][:5]:
            report_lines.append(f"• {item['Название товара']} ({item['Артикул']})")
            report_lines.append(f"  Продано: {item['Продано_упаковок']} уп., Поступило: {item['Поступлено_упаковок']} уп.")
            report_lines.append(f"  Разница: {item['Разница_упаковок']} уп. (излишек)")
    else:
        report_lines.append("Нет товаров с явным излишком")

    report_lines.append("\nСАМЫЕ ПРИБЫЛЬНЫЕ ТОВАРЫ:")
    report_lines.append("-" * 40)
    for item in insights['most_profitable']:
        profit_status = f"Прибыль: {item['Прибыль']:,.2f} руб." if item['Прибыль'] >= 0 else f"Убыток: {item['Прибыль']:,.2f} руб."
        report_lines.append(f"• {item['Название товара']} ({item['Артикул']})")
        report_lines.append(f"  {profit_status} | Рентабельность: {item['Рентабельность_%']:.2f}%")

    report_lines.append("\nНАИМЕНЕЕ ПРИБЫЛЬНЫЕ ТОВАРЫ:")
    report_lines.append("-" * 40)
    for item in insights['least_profitable']:
        profit_status = f"Прибыль: {item['Прибыль']:,.2f} руб." if item['Прибыль'] >= 0 else f"Убыток: {item['Прибыль']:,.2f} руб."
        report_lines.append(f"• {item['Название товара']} ({item['Артикул']})")
        report_lines.append(f"  {profit_status} | Рентабельность: {item['Рентабельность_%']:.2f}%")

    report_str = "\n".join(report_lines)
    print(report_str)
    save_report_to_file(report_str)  # Сохраняем в файл!
