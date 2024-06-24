import gradio as gr
from transformers import AutoTokenizer, TextStreamer
import torch
import time
from intel_extension_for_transformers.transformers import AutoModelForCausalLM

import pandas as pd
import util

found_matches = []

def csvs_to_string(file1,file2,file3):
    # 读取CSV文件
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    df3 = pd.read_csv(file3)

    # 将DataFrame转换为字符串
    str1 = df1.to_csv(index=False)
    str2 = df2.to_csv(index=False)
    str3 = df3.to_csv(index=False)

    # 将三个字符串合并成一个
    # combined_string = str1
    combined_string = str1 + "\n" + str2 + "\n" + str3

    return combined_string

# 假设CSV文件路径如下，调用函数
combined_csv_string = csvs_to_string('data/jiudian.csv','data/restaurants.csv','data/jingdian.csv')

words = util.load_data('data/location.csv', '地点')


# 加载模型和分词器
model_path = './chatglm3-6b-merge-lora'
model = AutoModelForCausalLM.from_pretrained(model_path, load_in_4bit=True, trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

chat_history = [
    {"role": "system", "content": "你是苏州的旅行助理。你要根据用户的偏好计划行程。在规划过程中，重要的是要考虑最省时、最合理的行程顺序，并简要介绍推荐的餐厅和景点。在规划时，最好提供具体的时间点计划，并考虑用户选择的交通方式（默认为公共交通）。"+combined_csv_string}
]
# chat_history = []
def user(user_message, history):
    # 更新历史记录
    history.append([user_message, None])
    return "", history
    #记录历史chat内容
def add_user_history(history,user_input):
    chat_history.append({"role": "User", "content": user_input})
    return chat_history
def add_response_history(history,response):
    chat_history.append({"role": "Assistant", "content": response})
    return chat_history

def bot(history):
    if not history[-1][0]:  # 如果没有用户输入，直接返回
        return history
    user_input = history[-1][0]
    if user_input == '生成路线' :
        output = history[-2][1]
        found_matches = util.find_matches(words, output)
        bot_message = ''
        for i in range(len(found_matches)-1):
            route = util.get_route(found_matches[i],found_matches[i+1])
            bot_message += route + '\n'
    else:
        
        context = "\n".join([h['content'] for h in chat_history])  # Extract previous conversations
        prompt = f"{context}\nUser: {user_input}\nAssistant:"
        # prompt = f"User: {user_input}\nAssistant:"
        inputs = tokenizer(prompt, return_tensors="pt").input_ids
        streamer = TextStreamer(tokenizer)
        outputs = model.generate(inputs, streamer=streamer)

        bot_message = tokenizer.decode(outputs[0], skip_special_tokens=True).split("Assistant:")[1].split("\nUser: ")[0].strip()
        # 查找匹配
        found_matches = util.find_matches(words, bot_message)
        # 打印或处理找到的匹配项
        print("找到的匹配项：", found_matches)

        add_user_history(chat_history,user_input)
        add_response_history(chat_history,bot_message)

    print(history)
    history[-1][1] = ""
    # 逐字生成响应
    for character in bot_message:
        history[-1][1] += character
        time.sleep(0.05)  # 控制字间延迟
        yield history

with gr.Blocks() as demo:
    gr.Markdown("# 苏州旅行小助手")
    
    # 用户和机器人头像的路径或URL
    user_avatar = "./images/1.jpeg"  # 替换为实际用户头像的路径
    bot_avatar = "./images/r.jpeg"    # 替换为实际机器人头像的路径
    chatbot = gr.Chatbot(height=500, avatar_images=[user_avatar, bot_avatar])
    msg = gr.Textbox(label="输入：")
    clear = gr.Button("清除")

    # 处理用户输入和机器人响应
    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    # 清除聊天历史
    clear.click(lambda: [], None, chatbot, queue=False)

demo.launch(server_port=8502, server_name='0.0.0.0')
