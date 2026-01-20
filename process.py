import pandas as pd
import numpy as np
from datetime import datetime
import logging
"""
Задаем настройки логирования, необходимые для отслеживания работы программы 
и быстрого определения где программа "сломалась", в случае если это произошло
"""
logging.basicConfig(level=logging.INFO) # Базовая конфигурация логирования, задающая минимальный уровень важности сообщений
logger = logging.getLogger(__name__)

def load_sales_data(file_path):
    """
    Загружает данные из CSV-файла.
    В конце своей работы возвращает DataFrame или None при ошибке.
    """
    try:
        # Пробуем разные кодировки и разделители
        try:
            df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            logger.info(f"Успешно загружено с UTF-8 и разделителем ';'")
        except:
            try:
                df = pd.read_csv(file_path, sep=',', encoding='utf-8')
                logger.info(f"Успешно загружено с UTF-8 и разделителем ','")
            except:
                try:
                    df = pd.read_csv(file_path, sep=';', encoding='cp1251')
                    logger.info(f"Успешно загружено с CP1251 и разделителем ';'")
                except:
                    df = pd.read_csv(file_path, sep=',', encoding='cp1251')
                    logger.info(f"Успешно загружено с CP1251 и разделителем ','")
          # Удаляем столбцы 'Unnamed:' если они есть
        unnamed_cols = [col for col in df.columns if 'Unnamed' in col]
        if unnamed_cols:
            df = df.drop(columns=unnamed_cols)
            logger.info(f"Удалены лишние столбцы: {unnamed_cols}")

        # Логируем доступные столбцы
        logger.info(f"Доступные столбцы: {list(df.columns)}")
        
        # Создаем словарь для переименования столбцов
        rename_dict = {}
        
        # Проверяем и переименовываем столбцы
        # Количество упаковок, шт. -> Количество упаковок
        if 'Количество упаковок, шт' in df.columns and 'Количество упаковок, шт.' not in df.columns:
            rename_dict['Количество упаковок, шт'] = 'Количество упаковок, шт.'
        # Операция -> Тип операции
        if 'Операция' in df.columns and 'Тип операции' not in df.columns:
            rename_dict['Операция'] = 'Тип операции'
        # Цена руб/шт -> Цена руб./шт.
        if 'Цена руб/шт' in df.columns and 'Цена руб./шт.' not in df.columns:
            rename_dict['Цена руб/шт'] = 'Цена руб./шт.'

        # Применяем переименование
        if rename_dict:
            df = df.rename(columns=rename_dict)
            logger.info(f"Переименованы столбцы: {rename_dict}")
        
        # Проверяем наличие всех необходимых столбцов после переименования
        required_columns = ['Дата', 'Артикул', 'Отдел товара', 'Количество упаковок, шт.', 
                          'Тип операции', 'Цена руб./шт.']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.error(f"ОТСУТСТВУЮТ ОБЯЗАТЕЛЬНЫЕ СТОЛБЦЫ: {missing_cols}")
            logger.info(f"Доступные столбцы после переименования: {list(df.columns)}")
            return None
        logger.info(f"Успешно загружено {len(df)} строк из {file_path}")
        return df
    except Exception as e:
        logger.error(f"НЕ УДАЛОСЬ ЗАГРУЗИТЬ ФАЙЛ {file_path}: {e}")
        return None

def preprocess_data(data):
    """
    Предобработка данных: проверяем наши данные, убираем лишнее, приводим все к одному формату,
    доваыляем необходимые столбцы.
    В конце своей работы возвращает DataFrame или None при ошибке.
    """
    if data is None or len(data) == 0:
        logger.error("НЕТ ДАННЫХ ДЛЯ ПЕРЕРАБОТКИ")
        return None
    df = data.copy()
    
    # 1. Преобразование даты
    try:
        df['Дата'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y', errors='coerce')
        invalid_dates = df['Дата'].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Удалено {invalid_dates} строк с некорректными датами")
            df = df.dropna(subset=['Дата'])
    except Exception as e:
        logger.error(f"ОШИБКА ПРЕОБРАЗОВАНИЯ ДАТЫ: {e}")
        return None
    # 2. Преобразование числовых столбцов
    numeric_cols = ['Количество упаковок, шт.', 'Цена руб./шт.']
    for col in numeric_cols:
        if col in df.columns:
            # У десятичных чисел производим замену запятых точками 
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # 3. Удаление строк с пустыми значениями
    initial_count = len(df)
    required_cols = ['Дата', 'Артикул', 'Отдел товара', 'Количество упаковок, шт.', 
                     'Тип операции', 'Цена руб./шт.']
    df = df.dropna(subset=required_cols)
    removed_count = initial_count - len(df)
    if removed_count > 0:
        logger.info(f"Удалено {removed_count} строк с пустыми значениями")
    # 4. Создание столбца "Сумма операции"
    df['Сумма операции'] = df['Количество упаковок, шт.'] * df['Цена руб./шт.']
    # 5. Проверка наличия отрицательных значений
    df = df[df['Количество упаковок, шт.'] >= 0]
    df = df[df['Цена руб./шт.'] >= 0]

    logger.info(f"Предобработка завершена. Осталось {len(df)} строк.")
    return df.reset_index(drop=True)

def get_operational_data(data_clean, operation_type=None):
    """
    Отфильтровать датасет по указанному типу операции, удалив ненужные строки. 
    Если тип не указан (None), вернуть исходный датасет.
    """
    if data_clean is None or len(data_clean) == 0:
        logger.warning("Нет данных для фильтрации.")
        return None
    
    if operation_type is None:
        return data_clean.copy()
    
    # Приводим operation_type к строке и проверяем существование значений
    valid_operations = data_clean['Тип операции'].unique()
    if operation_type not in valid_operations:
        logger.warning(f"Тип операции '{operation_type}' не найден. Доступные: {list(valid_operations)}")
        return None
    
    filtered_data = data_clean[data_clean['Тип операции'] == operation_type].copy()
    logger.info(f"Отфильтровано {len(filtered_data)} строк с типом операции '{operation_type}'")
    return filtered_data

def calculate_revenue_by_period(data_clean, period='D'):
    """
    Рассчитывает общую выручку для каждого указанного временного промежутка.
    """
    if data_clean is None or len(data_clean) == 0:
        logger.warning("Нет данных для расчёта выручки.")
        return None
    
    # Используем только продажи
    sales_data = get_operational_data(data_clean, operation_type='Продажа')
    if sales_data is None or len(sales_data) == 0:
        logger.warning("Нет данных о продажах для расчёта выручки.")
        return None
    
    try:
        # Группировка по периоду
        sales_data = sales_data.copy()
        sales_data['Период'] = sales_data['Дата'].dt.to_period(period)
        revenue_data = sales_data.groupby('Период').agg({
            'Сумма операции': 'sum'
        }).reset_index()
        
        # Преобразуем период обратно в дату для начала периода
        if period == 'D':
            revenue_data['Дата'] = revenue_data['Период'].dt.to_timestamp()
        elif period == 'W':
            revenue_data['Дата'] = revenue_data['Период'].dt.start_time
        elif period == 'M':
            revenue_data['Дата'] = revenue_data['Период'].dt.start_time
        
        revenue_data = revenue_data[['Дата', 'Сумма операции']]
        revenue_data = revenue_data.rename(columns={'Сумма операции': 'Выручка'})
        revenue_data = revenue_data.sort_values('Дата')
        
        logger.info(f"Выручка по периоду '{period}' рассчитана. {len(revenue_data)} периодов.")
        return revenue_data.reset_index(drop=True)
        
    except Exception as e:
        logger.error(f"ОШИБКА ПРИ РАСЧЁТЕ ВЫРУЧКИ ПО ПЕРИОДУ {period}: {e}")
        return None

def calculate_profit_by_period(data_clean, period='D'):
    """
    Рассчитывает прибыль (доходы - расходы) в периодах.
    """
    if data_clean is None or len(data_clean) == 0:
        logger.warning("Нет данных для расчёта прибыли.")
        return None
    
    try:
        # Получаем продажи и поступления
        sales = get_operational_data(data_clean, operation_type='Продажа')
        purchases = get_operational_data(data_clean, operation_type='Поступление')
        
        if sales is None or purchases is None:
            logger.warning("Нет данных о продажах или поступлениях.")
            return None
        
        sales = sales.copy()
        purchases = purchases.copy()
        
        # Добавляем период
        sales['Период'] = sales['Дата'].dt.to_period(period)
        purchases['Период'] = purchases['Дата'].dt.to_period(period)
        
        # Группируем продажи (доходы)
        revenue_by_period = sales.groupby('Период').agg({
            'Сумма операции': 'sum'
        }).reset_index()
        revenue_by_period = revenue_by_period.rename(columns={'Сумма операции': 'Доходы'})
        
        # Группируем поступления (расходы)
        expenses_by_period = purchases.groupby('Период').agg({
            'Сумма операции': 'sum'
        }).reset_index()
        expenses_by_period = expenses_by_period.rename(columns={'Сумма операции': 'Расходы'})
        
        # Объединяем
        profit_data = pd.merge(revenue_by_period, expenses_by_period, on='Период', how='outer').fillna(0)
        
        # Рассчитываем прибыль
        profit_data['Прибыль'] = profit_data['Доходы'] - profit_data['Расходы']
        
        # Преобразуем период в дату
        if period == 'D':
            profit_data['Дата'] = profit_data['Период'].dt.to_timestamp()
        elif period == 'W':
            profit_data['Дата'] = profit_data['Период'].dt.start_time
        elif period == 'M':
            profit_data['Дата'] = profit_data['Период'].dt.start_time
        
        profit_data = profit_data[['Дата', 'Прибыль']]
        profit_data = profit_data.sort_values('Дата')
        
        logger.info(f"Прибыль по периоду '{period}' рассчитана. {len(profit_data)} периодов.")
        return profit_data.reset_index(drop=True)
        
    except Exception as e:
        logger.error(f"ОШИБКА ПРИ РАСЧЁТЕ ПРИБЫЛИ ПО ПЕРИОДУ {period}: {e}")
        return None

def aggregate_sales_by_category(data_clean):
    """
    Группирует все данные по категориям товаров (“Отдел товаров”)
    и рассчитывает для каждой категории ключевые метрики.
    """
    if data_clean is None or len(data_clean) == 0:
        logger.warning("Нет данных для агрегации по категориям.")
        return None
    
    try:
        # Получаем только продажи
        sales_data = get_operational_data(data_clean, operation_type='Продажа')
        if sales_data is None or len(sales_data) == 0:
            logger.warning("Нет данных о продажах.")
            return None
        
        # Получаем только поступления
        purchase_data = get_operational_data(data_clean, operation_type='Поступление')
        
        # Группируем продажи по категориям
        sales_by_category = sales_data.groupby('Отдел товара').agg({
            'Сумма операции': 'sum',
            'Количество упаковок, шт.': 'sum',
            'Артикул': 'nunique'
        }).reset_index()
        
        sales_by_category = sales_by_category.rename(columns={
            'Сумма операции': 'Выручка',
            'Количество упаковок, шт.': 'Проданных_единиц',
            'Артикул': 'Уникальных_товаров'
        })
        
        # Группируем поступления по категориям (если есть)
        if purchase_data is not None and len(purchase_data) > 0:
            purchases_by_category = purchase_data.groupby('Отдел товара').agg({
                'Количество упаковок, шт.': 'sum'
            }).reset_index()
            purchases_by_category = purchases_by_category.rename(columns={
                'Количество упаковок, шт.': 'Поступило_единиц'
            })
            
            # Объединяем продажи и поступления
            category_stats = pd.merge(
                sales_by_category, 
                purchases_by_category, 
                on='Отдел товара', 
                how='left'
            ).fillna(0)
            
            # Рассчитываем остаток
            category_stats['Остаток_от_продаж'] = (
                category_stats['Проданных_единиц'] - category_stats['Поступило_единиц']
            )
        else:
            category_stats = sales_by_category
            category_stats['Остаток_от_продаж'] = category_stats['Проданных_единиц']
        
        # Сортировка по алфавиту
        category_stats = category_stats.sort_values('Отдел товара').reset_index(drop=True)
        
        logger.info(f"Агрегация по категориям завершена. {len(category_stats)} категорий.")
        return category_stats
        
    except Exception as e:
        logger.error(f"ОШИБКА ПРИ АШРЕГАЦИИ ПО КАТЕГОРИЯМ: {e}")
        return None

def get_top_n_products(data_clean, n=5, metric='quantity'):
    """
    Находит топ-N проданных товаров по выбранному критерию.
    """
    if data_clean is None or len(data_clean) == 0:
        logger.warning("Нет данных для поиска топ-продуктов.")
        return None
    
    # Проверяем допустимость метрики
    if metric not in ['quantity', 'revenue']:
        logger.error(f" НЕВЕРНАЯ МЕТРИКА: {metric}. Допустимо: 'quantity' или 'revenue'")
        return None
    
    try:
        # Получаем только продажи
        sales_data = get_operational_data(data_clean, operation_type='Продажа')
        if sales_data is None or len(sales_data) == 0:
            logger.warning("Нет данных о продажах.")
            return None
        
        # Группируем по товарам
        product_sales = sales_data.groupby(['Артикул', 'Название товара']).agg({
            'Сумма операции': 'sum',
            'Количество упаковок, шт.': 'sum'
        }).reset_index()
        
        product_sales = product_sales.rename(columns={
            'Сумма операции': 'Выручка',
            'Количество упаковок, шт.': 'Кол-во_упаковок'
        })
        
        # Сортировка по выбранной метрике
        if metric == 'quantity':
            top_products = product_sales.sort_values('Кол-во_упаковок', ascending=False).head(n)
        else:  # metric == 'revenue'
            top_products = product_sales.sort_values('Выручка', ascending=False).head(n)
        
        logger.info(f"Топ-{n} продуктов по {metric} найдено.")
        return top_products.reset_index(drop=True)
        
    except Exception as e:
        logger.error(f"ОШИБКА ПРИ ПОИСКЕ ТОП-ПРОДУКТОВ: {e}")
        return None

def analyze_inventory_turnover(data_clean, top_n=10):
    """
    Анализирует движение товаров, сопоставляя объёмы продаж и поступлений
    по каждому товару (артикулу).
    """
    if data_clean is None or len(data_clean) == 0:
        logger.warning("Нет данных для анализа оборачиваемости.")
        return None
    
    try:
        # Получаем продажи
        sales = get_operational_data(data_clean, operation_type='Продажа')
        if sales is None or len(sales) == 0:
            logger.warning("Нет данных о продажах.")
            return None
        
        # Получаем поступления
        purchases = get_operational_data(data_clean, operation_type='Поступление')
        if purchases is None or len(purchases) == 0:
            logger.warning("Нет данных о поступлениях.")
            return None
        
        # Группируем продажи по товарам
        sales_by_product = sales.groupby(['Артикул', 'Название товара']).agg({
            'Количество упаковок, шт.': 'sum',
            'Сумма операции': 'sum'
        }).reset_index()
        sales_by_product = sales_by_product.rename(columns={
            'Количество упаковок, шт.': 'Продано_упаковок',
            'Сумма операции': 'Выручка_от_продаж'
        })
        
        # Группируем поступления по товарам
        purchases_by_product = purchases.groupby(['Артикул', 'Название товара']).agg({
            'Количество упаковок, шт.': 'sum'
        }).reset_index()
        purchases_by_product = purchases_by_product.rename(columns={
            'Количество упаковок, шт.': 'Поступлено_упаковок'
        })
        
        # Объединяем
        inventory_analysis = pd.merge(
            sales_by_product,
            purchases_by_product,
            on=['Артикул', 'Название товара'],
            how='outer'
        ).fillna(0)
        
        # Рассчитываем разницу
        inventory_analysis['Разница_упаковок'] = (
            inventory_analysis['Продано_упаковок'] - inventory_analysis['Поступлено_упаковок']
        )
        
        # Сортируем по абсолютному значению разницы
        inventory_analysis['Абс_разница'] = inventory_analysis['Разница_упаковок'].abs()
        inventory_analysis = inventory_analysis.sort_values('Абс_разница', ascending=False).head(top_n)
        inventory_analysis = inventory_analysis.drop(columns=['Абс_разница'])

        logger.info(f"Анализ оборачиваемости завершён. Топ-{top_n} товаров.")
        return inventory_analysis.reset_index(drop=True)
        
    except Exception as e:
        logger.error(f"ОШИБКА ПРИ АНАЛИЗЕ ОБОРАЧИВАЕМОСТИ: {e}")
        return None 
    
def calculate_reorder_point(lead_time_days, avg_daily_sales, safety_stock):
    """
    Рассчитывает точку заказа (reorder point).
    :param lead_time_days: Время выполнения заказа в днях
    :param avg_daily_sales: Среднесуточные продажи
    :param safety_stock: Запас безопасности
    :return: Точка заказа (целое число)
    """
    return int(lead_time_days * avg_daily_sales + safety_stock)
    
def identify_slow_moving_items(data, days_back=90, sales_threshold=5):
    """
    Выявляет товары, которые "застоялись" на складе — мало продаются, но есть в остатках.
    Параметры:
        data (pd.DataFrame): Очищенные данные из InventoryManager.data_clean
        days_back (int): Количество дней назад, за которые анализируется спрос (по умолчанию 90)
        sales_threshold (int): Максимальное количество проданных упаковок за период, 
                              после которого товар считается "медленно движущимся" (по умолчанию 5)
    Возвращает:
        pd.DataFrame: Таблица с товарами, которые нужно "разогнать"
                     Столбцы: 'Артикул', 'Название товара', 'Продано за период', 'Текущий остаток', 'Дней с последней продажи'
    """
    if data is None or len(data) == 0:
        return pd.DataFrame()

    # Определяем дату начала анализа
    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days_back)

    # Фильтруем только продажи за последние N дней
    sales_data = data[
        (data['Тип операции'] == 'Продажа') & 
        (data['Дата'] >= cutoff_date)
    ].copy()

    # Группируем по товару: суммируем продажи
    sales_summary = sales_data.groupby(['Артикул', 'Название товара'])['Количество упаковок, шт.'].sum().reset_index()
    sales_summary.rename(columns={'Количество упаковок, шт.': 'Продано за период'}, inplace=True)

    # Мы не храним баланс в исходных данных — нужно посчитать: Поступления - Продажи по каждому артикулу
    # Создаём общий свод по каждому товару
    all_data = data.copy()
    # Продажи
    sales_by_sku = all_data[all_data['Тип операции'] == 'Продажа'].groupby(['Артикул', 'Название товара'])['Количество упаковок, шт.'].sum().reset_index()
    sales_by_sku.rename(columns={'Количество упаковок, шт.': 'Продано_всего'}, inplace=True)
    
    # Поступления
    purchases_by_sku = all_data[all_data['Тип операции'] == 'Поступление'].groupby(['Артикул', 'Название товара'])['Количество упаковок, шт.'].sum().reset_index()
    purchases_by_sku.rename(columns={'Количество упаковок, шт.': 'Поступлено_всего'}, inplace=True)
    
    # Объединяем: текущий остаток = Поступления - Продажи
    inventory = sales_by_sku.merge(purchases_by_sku, on=['Артикул', 'Название товара'], how='outer').fillna(0)
    inventory['Текущий остаток'] = inventory['Поступлено_всего'] - inventory['Продано_всего']
    
    # Оставляем только товары с остатком > 0
    inventory = inventory[inventory['Текущий остаток'] > 0]

    # Объединяем с продажами за последние 90 дней
    merged = inventory.merge(sales_summary, on=['Артикул', 'Название товара'], how='left').fillna(0)

    # Фильтруем: продажи <= порога
    slow_moving = merged[merged['Продано за период'] <= sales_threshold].copy()

    # Добавляем: "Дней с последней продажи"
    last_sale_dates = sales_data.groupby(['Артикул', 'Название товара'])['Дата'].max().reset_index()
    last_sale_dates['Дней с последней продажи'] = (pd.Timestamp.now() - last_sale_dates['Дата']).dt.days
    slow_moving = slow_moving.merge(last_sale_dates[['Артикул', 'Название товара', 'Дней с последней продажи']], on=['Артикул', 'Название товара'], how='left')

    # Сортируем
    slow_moving = slow_moving.sort_values(['Продано за период', 'Дней с последней продажи'], ascending=[True, False])
    
    return slow_moving[['Артикул', 'Название товара', 'Продано за период', 'Текущий остаток', 'Дней с последней продажи']].reset_index(drop=True)
