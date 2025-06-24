import csv
import os


CSV_FILENAME = "layout.csv"
OUTPUT_FILENAME = "templates/seatmap.svg"


CELL_SIZE = 50      
SEAT_SIZE = 35       
PADDING = 50      

def generate_svg_from_csv():
    """CSVファイルから座席情報を読み込み、間隔を空けてSVGファイルを生成する"""
    seats = []
    
    try:
        with open(CSV_FILENAME, mode='r', encoding='utf-8') as f:
            try:
                next(f)
            except StopIteration:
                pass 
            reader = csv.reader(f)
            for row in reader:
                if not row: continue
                try:
                    seat_id = int(row[0])
                   
                    grid_x = int(row[1])
                    grid_y = int(row[2])
                    seats.append({'id': seat_id, 'grid_x': grid_x, 'grid_y': grid_y})
                except (ValueError, IndexError) as e:
                    print(f"警告: CSVファイルの行をスキップしました (データ形式エラー): {row} - {e}")
                    
    except FileNotFoundError:
        print(f"エラー: '{CSV_FILENAME}' が見つかりません。ファイル名と場所を確認してください。")
        return 0
    
    if not seats:
        print("エラー: CSVから座席データを読み込めませんでした。")
        return 0

    max_grid_x = max(s['grid_x'] for s in seats)
    max_grid_y = max(s['grid_y'] for s in seats)
    canvas_width = (max_grid_x * CELL_SIZE) + PADDING * 2
    canvas_height = (max_grid_y * CELL_SIZE) + PADDING * 2

    svg_elements = []
    for seat in seats:
        seat_id = seat['id']
        
      
        svg_x = seat['grid_x'] * CELL_SIZE
        svg_y = seat['grid_y'] * CELL_SIZE
        
        if 1 <= seat_id <= 20:
            css_class = "seat yellow-seat"
        else:
            css_class = "seat blue-seat"
        
        svg_element_string = (
            f'<rect id="seat-{seat_id}" class="{css_class}" '
            f'x="{svg_x}" y="{svg_y}" '
            f'width="{SEAT_SIZE}" height="{SEAT_SIZE}" rx="5"/>'
        )
        svg_elements.append(svg_element_string)

    svg_header = f'<svg width="{canvas_width}" height="{canvas_height}" xmlns="http://www.w3.org/2000/svg">\n<g transform="translate({PADDING}, {PADDING})">\n'
    svg_footer = '\n</g>\n</svg>'
    
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    with open(OUTPUT_FILENAME, "w", encoding='utf-8') as f:
        f.write(svg_header)
        f.write("\n".join(svg_elements))
        f.write(svg_footer)

    total_seats = len(seats)
    print(f"完了！CSVに基づいたSVGファイル（{total_seats}席）が '{OUTPUT_FILENAME}' に生成されました。")
    return total_seats

if __name__ == "__main__":
    generate_svg_from_csv()
