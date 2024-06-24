import requests
import pandas as pd
import re


# 加载CSV文件
def load_data(file_path, column_name):
    df = pd.read_csv(file_path)
    # 确保提取的列转换为字符串类型
    return df[column_name].astype(str)
# 在文本中找到所有匹配的单词或短语
def find_matches(words, text):
    matches = []
    for word in words:
        # 使用正则表达式搜索，考虑到大小写不敏感
        if re.search(re.escape(word), text, re.IGNORECASE):
            matches.append(word)
    return matches

my_key = ''
def search_amap_place(keywords, region, user_key):

    url = "https://restapi.amap.com/v5/place/text"
    params = {
        'keywords': keywords,
        'types': '0512',  # 该类型代码指代某种具体类别，根据需求更改
        'region': region,
        'key': user_key
    }
    
    response = requests.get(url, params=params).json()
    print(response)
    if response['status'] == '0' or response['count'] == '0':
        return '',''
    # print(response)
    # citycode = response['pois'][0]['citycode']
    address = response['pois'][0]['address']
    location = response['pois'][0]['location']
    
    return address ,location # 解析返回的JSON数据


def describe_first_transit_route(origin, destination, city1, city2, user_key):
    
    url = "https://restapi.amap.com/v5/direction/transit/integrated"
    params = {
        'origin': origin,
        'destination': destination,
        'city1': city1,
        'city2': city2,
        'key': user_key
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    description = ""

    def format_distance(distance):
        """将距离转换为适当的单位显示"""
        distance = int(distance)
        if distance >= 1000:
            return f"{distance / 1000:.1f}km"
        else:
            return f"{distance}米"

    if data['status'] == '1' and 'route' in data and 'transits' in data['route']:
        routes = data['route']['transits']
        if routes:
            route = routes[0]  # 只取第一个路线
            total_distance = format_distance(route['distance'])
            walking_distance = format_distance(route['walking_distance'])
            
            description += f"建议路线总距离为 {total_distance}，其中步行距离为 {walking_distance}。"
            
            for j, segment in enumerate(route['segments']):
                if 'walking' in segment:
                    walking = segment['walking']
                    walk_distance = format_distance(walking['distance'])
                    description += f" 第{j + 1}段步行距离 {walk_distance}。"
                
                if 'bus' in segment:
                    bus = segment['bus']
                    for busline in bus['buslines']:
                        bus_distance = format_distance(busline['distance'])
                        description += f" 乘坐公交线路 {busline['name']}，从 {busline['departure_stop']['name']} 出发，到 {busline['arrival_stop']['name']} 下车，途径 {busline['via_num']} 站，行驶距离 {bus_distance}。"
                        
            if route['nightflag'] == '1':
                description += " 该路线包含夜班车服务。"
        else:
            description = "没有可用的路线信息。"
    else:
        description = f"API调用失败或没有找到路线，错误信息：{data.get('info', '无数据')}"

    return description




def get_route(keyword1,keyword2):
    user_key = my_key
    # keywords = "拙政园"
    region = "苏州市"
    address1 ,location1 = search_amap_place(keyword1, region, user_key)
    address2 ,location2 = search_amap_place(keyword2, region, user_key)

    # print( address ,location)

    # 示例使用
    origin = location1
    destination = location2
    city1 = "0512"
    city2 = "0512"
    user_key = my_key

    route_description = keyword1 + '->' +keyword2 + ':'+ describe_first_transit_route(origin, destination, city1, city2, user_key)
    # print(route_description)
    return route_description
