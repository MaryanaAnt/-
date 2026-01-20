import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from process import (
    load_sales_data,
    preprocess_data,
    calculate_revenue_by_period,
    calculate_profit_by_period,
    aggregate_sales_by_category,
    get_top_n_products,
    analyze_inventory_turnover
)
from process import (
    get_operational_data,
    calculate_revenue_by_period,
    calculate_reorder_point,
    identify_slow_moving_items  # ← НОВАЯ ФУНКЦИЯ
)

class InventoryManager:
    def __init__(self):
        self.data = None
        self.data_clean = None
        # Настройка стиля графиков
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")

    def load_data(self, file_path):
        print(f" Загрузка данных из: {file_path}")
        self.data = load_sales_data(file_path)
        if self.data is None:
            print("ЗАГРУЗКА ДАННЫХ НЕ УДАЛАСЬ")
            return False
        return True

    def preprocess(self):
        if self.data is None:
            print("НЕТ ДАННЫХ ДЛЯ ПЕРЕРАБОТКИ. СНАЧАЛА ЗАГРУЗИТЕ ФАЙЛ.")
            return False
        print("Предобработка данных...")
        self.data_clean = preprocess_data(self.data)
        if self.data_clean is None:
            print("ПЕРЕРАБОТКА НЕ УДАЛАСЬ.")
            return False
        print(f"Предобработка завершена. Обработано {len(self.data_clean)} строк.")
        return True

    def analyze_revenue(self, period='D'):
        if self.data_clean is None:
            print("НЕТ ПЕРЕРАБОТАННЫХ ДАННЫХ. Вызовите .preprocess() сначала.")
            return None
        print(f" Расчёт выручки по периоду: {period}")
        return calculate_revenue_by_period(self.data_clean, period)

    def analyze_profit(self, period='D'):
        if self.data_clean is None:
            print("НЕТ ПЕРЕРАБОТАННЫХ ДАННЫХ.")
            return None
        print(f"Расчёт прибыли по периоду: {period}")
        return calculate_profit_by_period(self.data_clean, period)

    def analyze_by_category(self):
        if self.data_clean is None:
            print("НЕТ ПЕРЕРАБОТАННЫХ ДАННЫХ.")
            return None
        print("Анализ продаж по отделам...")
        return aggregate_sales_by_category(self.data_clean)

    def top_products(self, n=5, metric='quantity'):
        if self.data_clean is None:
            print("НЕТ ПЕРЕРАБОТАННЫХ ДАННЫХ.")
            return None
        print(f"Топ-{n} товаров по {metric}...")
        return get_top_n_products(self.data_clean, n, metric)

    def inventory_turnover(self, top_n=10):
        if self.data_clean is None:
            print("НЕТ ПЕРЕРАБОТАННЫХ ДАННЫХ.")
            return None
        print(f"Анализ оборачиваемости товаров (топ-{top_n})...")
        return analyze_inventory_turnover(self.data_clean, top_n)

    # --- МЕТОДЫ ВИЗУАЛИЗАЦИИ ---
    
    def plot_revenue_trend(self, period='D', save_path=None):
        """
        Визуализация тренда выручки по времени.
        """
        if self.data_clean is None:
            print("НЕТ ДАННЫХ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        revenue_data = self.analyze_revenue(period)
        if revenue_data is None or revenue_data.empty:
            print("НЕТ ДАННЫХ О ВЫРУЧКЕ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        plt.figure(figsize=(14, 6))
        
        # Определяем название периода для заголовка
        period_names = {'D': 'дням', 'W': 'неделям', 'M': 'месяцам'}
        period_name = period_names.get(period, 'дням')
        
        plt.plot(revenue_data['Дата'], revenue_data['Выручка'] / 1_000_000, 
                marker='o', linewidth=2, markersize=6)
        plt.title(f'Тренд выручки по {period_name}', fontsize=16, fontweight='bold')
        plt.xlabel('Дата', fontsize=12)
        plt.ylabel('Выручка (млн руб.)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f" График сохранён: {save_path}")
        
        plt.show()
        return revenue_data
    
    def plot_profit_trend(self, period='D', save_path=None):
        """
        Визуализация тренда прибыли по времени.
        """
        if self.data_clean is None:
            print("НЕТ ДАННЫХ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        profit_data = self.analyze_profit(period)
        if profit_data is None or profit_data.empty:
            print("НЕТ ДАННЫХ О ПРИБЫЛИ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        plt.figure(figsize=(14, 6))
        
        period_names = {'D': 'дням', 'W': 'неделям', 'M': 'месяцам'}
        period_name = period_names.get(period, 'дням')
        
        colors = ['green' if p >= 0 else 'red' for p in profit_data['Прибыль']]
        bars = plt.bar(profit_data['Дата'], profit_data['Прибыль'] / 1_000_000, 
                      color=colors, alpha=0.7)
        
        plt.title(f'Прибыль по {period_name}', fontsize=16, fontweight='bold')
        plt.xlabel('Дата', fontsize=12)
        plt.ylabel('Прибыль (млн руб.)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Добавляем подписи значений
        for bar in bars:
            height = bar.get_height()
            if abs(height) > 0.1:  # Показываем только значительные значения
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}', ha='center', va='bottom' if height >= 0 else 'top',
                        fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f" График сохранён: {save_path}")
        
        plt.show()
        return profit_data
    
    def plot_category_sales(self, metric='Выручка', save_path=None):
        """
        Визуализация продаж по категориям.
        """
        if self.data_clean is None:
            print("НЕТ ДАННЫХ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        category_data = self.analyze_by_category()
        if category_data is None or category_data.empty:
            print("НЕТ ДАННЫХ ПО КАТЕГОРИЯМ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Столбчатая диаграмма
        bars1 = ax1.bar(category_data['Отдел товара'], 
                       category_data[metric] / 1_000_000, 
                       color=sns.color_palette("husl", len(category_data)))
        ax1.set_title(f'{metric} по отделам', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Отдел товара', fontsize=12)
        ax1.set_ylabel(f'{metric} (млн руб.)', fontsize=12)
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Добавляем значения на столбцы
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=10)
        
        # Круговая диаграмма
        ax2.pie(category_data[metric], labels=category_data['Отдел товара'],
               autopct='%1.1f%%', startangle=90, colors=sns.color_palette("husl", len(category_data)))
        ax2.set_title(f'Доля отделов в {metric.lower()}', fontsize=14, fontweight='bold')
        ax2.axis('equal')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"График сохранён: {save_path}")
        
        plt.show()
        return category_data
    
    def plot_top_products_chart(self, n=5, metric='quantity', save_path=None):
        """
        Визуализация топ-N товаров.
        """
        if self.data_clean is None:
            print("НЕТ ДАННЫХ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        top_products = self.top_products(n, metric)
        if top_products is None or top_products.empty:
            print("НЕТ ДАННЫХ О ТОП-ТОВАРАХ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        plt.figure(figsize=(12, 6))
        
        # Создаем метки для товаров
        labels = [f"{row['Название товара']}\n(арт. {row['Артикул']})" 
                 for _, row in top_products.iterrows()]
        
        if metric == 'quantity':
            values = top_products['Кол-во_упаковок']
            title = f'Топ-{n} товаров по количеству продаж'
            ylabel = 'Количество упаковок, шт.'
        else:
            values = top_products['Выручка'] / 1_000_000
            title = f'Топ-{n} товаров по выручке'
            ylabel = 'Выручка (млн руб.)'
        
        bars = plt.barh(labels, values, color=sns.color_palette("viridis", len(top_products)))
        plt.gca().invert_yaxis()  # Переворачиваем для лучшего отображения
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel(ylabel, fontsize=12)
        
        # Добавляем значения на столбцы
        for bar in bars:
            width = bar.get_width()
            if metric == 'revenue':
                label = f'{width:.1f}'
            else:
                label = f'{int(width):,}'.replace(',', ' ')
            plt.text(width * 1.01, bar.get_y() + bar.get_height()/2.,
                    label, va='center', fontsize=10)
        
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"График сохранён: {save_path}")
        
        plt.show()
        return top_products
    
    def plot_inventory_turnover_chart(self, top_n=10, save_path=None):
        """
        Визуализация анализа оборачиваемости товаров.
        """
        if self.data_clean is None:
            print("НЕТ ДАННЫХ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        turnover_data = self.inventory_turnover(top_n)
        if turnover_data is None or turnover_data.empty:
            print("НЕТ ДАННЫХ ОБ ОБОРАЧИВАЕМОСТИ ДЛЯ ВИЗУАЛИЗАЦИИ.")
            return None
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # График продаж и поступлений
        x = range(len(turnover_data))
        bar_width = 0.35
        
        bars1 = ax1.bar([i - bar_width/2 for i in x], turnover_data['Продано_упаковок'], 
                       bar_width, label='Продано', alpha=0.7, color='green')
        bars2 = ax1.bar([i + bar_width/2 for i in x], turnover_data['Поступлено_упаковок'], 
                       bar_width, label='Поступило', alpha=0.7, color='blue')
        
        ax1.set_xlabel('Товары', fontsize=12)
        ax1.set_ylabel('Количество упаковок', fontsize=12)
        ax1.set_title('Сравнение продаж и поступлений по товарам', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        # Сокращаем названия для лучшего отображения
        short_labels = [f"Арт. {row['Артикул']}" for _, row in turnover_data.iterrows()]
        ax1.set_xticklabels(short_labels, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # График разницы
        colors = ['green' if val >= 0 else 'red' for val in turnover_data['Разница_упаковок']]
        bars3 = ax2.bar(short_labels, turnover_data['Разница_упаковок'], color=colors, alpha=0.7)
        ax2.set_xlabel('Товары', fontsize=12)
        ax2.set_ylabel('Разница (Продано - Поступило)', fontsize=12)
        ax2.set_title('Разница между продажами и поступлениями', fontsize=14, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Добавляем значения на столбцы
        for bar in bars3:
            height = bar.get_height()
            if abs(height) > 100:  # Показываем только значительные значения
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height):,}'.replace(',', ' '),
                        ha='center', va='bottom' if height >= 0 else 'top',
                        fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"График сохранён: {save_path}")
        
        plt.show()
        return turnover_data
    
    def create_comprehensive_report(self, output_dir='reports'):
        """
        Создает комплексный отчет со всеми визуализациями.
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n{'='*60}")
        print("СОЗДАНИЕ КОМПЛЕКСНОГО ОТЧЕТА С ВИЗУАЛИЗАЦИЕЙ")
        print('='*60)
        
        # 1. Тренд выручки
        self.plot_revenue_trend(save_path=f"{output_dir}/revenue_trend.png")
        
        # 2. Тренд прибыли
        self.plot_profit_trend(save_path=f"{output_dir}/profit_trend.png")
        
        # 3. Анализ по категориям
        self.plot_category_sales(save_path=f"{output_dir}/category_analysis.png")
        
        # 4. Топ товары по количеству
        self.plot_top_products_chart(n=5, metric='quantity', 
                                   save_path=f"{output_dir}/top_products_quantity.png")
        
        # 5. Топ товары по выручке
        self.plot_top_products_chart(n=5, metric='revenue', 
                                   save_path=f"{output_dir}/top_products_revenue.png")
        
        # 6. Оборачиваемость
        self.plot_inventory_turnover_chart(top_n=10, 
                                          save_path=f"{output_dir}/inventory_turnover.png")
        
         # 7. Медленно движущиеся товары
        slow_moving = self.get_slow_moving_items_report(days_back=90, sales_threshold=5)
        if slow_moving is not None and not slow_moving.empty:
            self.plot_slow_moving_items(slow_moving, save_path=f"{output_dir}/slow_moving_items.png")
        else:
            print(" Нет данных для визуализации медленно движущихся товаров.")

        print(f"\n Все графики сохранены в папке: {output_dir}/")
        print("Визуализация завершена!")

    def get_slow_moving_items_report(self, days_back=90, sales_threshold=5):
        """
    Возвращает отчет о товарах, которые "застоялись" на складе.
    
    Это ключевой отчет для закупщиков и менеджеров склада.
    Позволяет:
    - Выявить товары, требующие акций или вывода из ассортимента
    - Освободить складские площади
    - Снизить издержки на хранение
    
    Пример использования:
        report = manager.get_slow_moving_items_report(days_back=60, sales_threshold=3)
        print(report)
        """
        return identify_slow_moving_items(
            self.data_clean, 
            days_back=days_back, 
            sales_threshold=sales_threshold
        )
    
    def plot_slow_moving_items(self, slow_moving, save_path=None):
        """
        Визуализирует медленно движущиеся товары: горизонтальный бар-чарт.
        Продажи за 90 дней vs текущий остаток.
        """
        if slow_moving.empty:
            print("⚠️ Нет данных для визуализации медленно движущихся товаров.")
            return None

        # Сортируем по остатку (убывание) — самые "застоявшиеся" наверху
        slow_moving = slow_moving.sort_values('Текущий остаток', ascending=False).reset_index(drop=True)

        # Подготовка данных
        labels = [f"{row['Название товара']}\n(арт. {row['Артикул']})" 
                 for _, row in slow_moving.iterrows()]
        sales = slow_moving['Продано за период']
        stock = slow_moving['Текущий остаток']

        # Настройка графика
        fig, ax = plt.subplots(figsize=(14, max(8, len(slow_moving) * 0.5)))  # Динамическая высота
        y_pos = range(len(slow_moving))

        # Горизонтальные столбики
        bar_height = 0.35
        ax.barh([y - bar_height/2 for y in y_pos], sales, 
                height=bar_height, label='Продано за 90 дней', color='orange', alpha=0.8)
        ax.barh([y + bar_height/2 for y in y_pos], stock, 
                height=bar_height, label='Текущий остаток', color='red', alpha=0.8)

        # Подписи оси Y — названия товаров
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=10, ha='right')
        
        # Подписи на столбцах — только если значение > 0
        for i, (s, st) in enumerate(zip(sales, stock)):
            if s > 0:
                ax.text(s + 0.5, i - bar_height/2, f'{int(s)}', 
                        va='center', ha='left', fontsize=9, fontweight='bold', color='darkorange')
            if st > 0:
                ax.text(st + 0.5, i + bar_height/2, f'{int(st)}', 
                        va='center', ha='left', fontsize=9, fontweight='bold', color='darkred')

        # Стиль графика
        ax.set_title('Медленно движущиеся товары: продажи за 90 дней vs текущий остаток', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Количество упаковок', fontsize=12)
        ax.legend(loc='lower right', fontsize=11)
        ax.grid(axis='x', alpha=0.3, linestyle='--')

        # Улучшаем отступы
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"📈 График медленно движущихся товаров сохранён: {save_path}")

        plt.show()
        return slow_moving
