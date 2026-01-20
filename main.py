import os
from manager import InventoryManager
import pandas as pd

def save_report_to_file(report_text, filename="inventory_report.txt"):
    """Сохраняет отчёт в текстовый файл."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f" Отчёт сохранён в файл: {filename}")

def main():
    print(" Система анализа продаж и инвентаря\n" + "="*50)

    # Инициализация менеджера
    manager = InventoryManager()

    # Загрузка данных
    files = ["Данные 1.csv", "Данные 2.csv"]
    all_data = []

    for file in files:
        if os.path.exists(file):
            if manager.load_data(file):
                all_data.append(manager.data)
                print(f" Файл {file} успешно загружен.")
        else:
            print(f"Файл {file} не найден. Пропущен.")

    if not all_data:
        print(" НИ ОДИН ФАЙЛ НЕ БЫЛ ЗАГРУЖЕН. ЗАВЕРШЕНИЕ.")
        return

    # Объединяем данные
    manager.data = pd.concat(all_data, ignore_index=True)
    print(f" Объединено {len(manager.data)} строк из {len([f for f in files if os.path.exists(f)])} файлов.")

    # Предобработка
    if not manager.preprocess():
        print("ПЕРЕРАБОТКА ДАННЫХ НЕ УДАЛАСЬ. ЗАВЕРШЕНИЕ.")
        return

    # Проверка на минимальный объём данных
    if len(manager.data_clean) < 10:
        print("СЛИШКОМ МАЛО ДАННЫХ ДЛЯ АНАЛИЗА. ЗАВЕРШЕНИЕ.")
        return

    # Анализ
    print("\n" + "="*50)
    print("НАЧАЛО АНАЛИЗА")
    
    # Выручка и прибыль
    revenue = manager.analyze_revenue(period='D')
    profit = manager.analyze_profit(period='D')

    # Анализ по категориям
    category_stats = manager.analyze_by_category()

    # Топ-5 товаров по продажам
    top_products_qty = manager.top_products(n=5, metric='quantity')
    top_products_rev = manager.top_products(n=5, metric='revenue')

    # Оборачиваемость
    turnover_analysis = manager.inventory_turnover(top_n=10)

    # Формирование текстового отчёта
    report = []

    report.append("ОТЧЁТ ПО АНАЛИЗУ ПРОДАЖ И ИНВЕНТАРЯ")
    report.append("="*70)
    report.append(f"Дата генерации: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Обработано строк: {len(manager.data_clean)}")
    report.append("")

    # Выручка
    if revenue is not None and not revenue.empty:
        report.append(" ВЫРУЧКА ПО ДНЯМ (первые 10 записей):")
        report.append(revenue.head(10).to_string(index=False))
        report.append("")
    else:
        report.append("НЕТ ДАННЫХ О ВЫРУЧКЕ.")

    # Прибыль
    if profit is not None and not profit.empty:
        report.append("💰 ПРИБЫЛЬ ПО ДНЯМ (первые 10 записей):")
        report.append(profit.head(10).to_string(index=False))
        report.append("")
    else:
        report.append("НЕТ ДАННЫХ О ПРИБЫЛИ.")

    # Категории
    if category_stats is not None and not category_stats.empty:
        report.append(" ПРОДАЖИ ПО ОТДЕЛАМ:")
        report.append(category_stats.to_string())
        report.append("")

    # Топ-5 по количеству
    if top_products_qty is not None and not top_products_qty.empty:
        report.append(" ТОП-5 ТОВАРОВ ПО КОЛИЧЕСТВУ ПРОДАННЫХ ЕДИНИЦ:")
        report.append(top_products_qty.to_string(index=False))
        report.append("")

    # Топ-5 по выручке
    if top_products_rev is not None and not top_products_rev.empty:
        report.append(" ТОП-5 ТОВАРОВ ПО ВЫРУЧКЕ:")
        report.append(top_products_rev.to_string(index=False))
        report.append("")

    # Оборачиваемость
    if turnover_analysis is not None and not turnover_analysis.empty:
        report.append(" АНАЛИЗ ОБОРАЧИВАЕМОСТИ ТОВАРОВ (ТОП-10):")
        report.append(turnover_analysis.to_string(index=False))
        report.append("")

    report.append(" АНАЛИЗ ЗАВЕРШЁН.")

    # Сохранение текстового отчёта
    save_report_to_file("\n".join(report))
    
    # --- ВИЗУАЛИЗАЦИЯ ---
    print("\n" + "="*50)
    print(" ГЕНЕРАЦИЯ ГРАФИКОВ И ВИЗУАЛИЗАЦИЙ")
    print("="*50)
    
    # Создание всех графиков
    manager.create_comprehensive_report(output_dir='sales_visualizations')
    
    # Или можно вызывать отдельные графики:
    # manager.plot_revenue_trend()
    # manager.plot_category_sales()
    # manager.plot_top_products_chart(n=5, metric='revenue')
    # manager.plot_inventory_turnover_chart(top_n=10)

    print("\n" + "="*50)
    print(" ПРОГРАММА УСПЕШНО ЗАВЕРШЕНА!")
    print(" Текстовый отчёт: inventory_report.txt")
    print(" Визуализации: папка 'sales_visualizations/'")
    print("="*50)

if __name__ == "__main__":
    main()
