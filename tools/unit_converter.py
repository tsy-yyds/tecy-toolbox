# -*- coding: utf-8 -*-
"""
单位换算工具
"""

import customtkinter as ctk


class UnitConverterFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.create_widgets()

    def create_widgets(self):
        # 标题
        title = ctk.CTkLabel(self, text="📐 单位换算器", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(10, 15))

        # 类别选择
        category_frame = ctk.CTkFrame(self)
        category_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(category_frame, text="换算类别：", font=ctk.CTkFont(size=14)).pack(side="left", padx=10, pady=10)

        self.category_var = ctk.StringVar(value="长度")
        categories = ["长度", "重量", "面积", "体积", "温度", "时间", "速度", "数据存储"]
        self.category_menu = ctk.CTkOptionMenu(
            category_frame,
            values=categories,
            variable=self.category_var,
            width=200,
            command=self.on_category_change
        )
        self.category_menu.pack(side="left", padx=5, pady=10)

        # 换算区域
        convert_frame = ctk.CTkFrame(self)
        convert_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 输入单位
        input_frame = ctk.CTkFrame(convert_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(input_frame, text="输入：", font=ctk.CTkFont(size=14, weight="bold"), width=60).pack(side="left")

        self.input_entry = ctk.CTkEntry(input_frame, width=200, font=ctk.CTkFont(size=16))
        self.input_entry.pack(side="left", padx=5)
        self.input_entry.insert(0, "1")

        self.input_unit = ctk.StringVar(value="米")
        self.input_menu = ctk.CTkOptionMenu(input_frame, values=["米"], variable=self.input_unit, width=150)
        self.input_menu.pack(side="left", padx=5)

        # 交换按钮
        swap_frame = ctk.CTkFrame(convert_frame, fg_color="transparent")
        swap_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(swap_frame, text="⇅ 交换单位", width=150, command=self.swap_units).pack()

        # 输出单位
        output_frame = ctk.CTkFrame(convert_frame, fg_color="transparent")
        output_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(output_frame, text="结果：", font=ctk.CTkFont(size=14, weight="bold"), width=60).pack(side="left")

        self.output_entry = ctk.CTkEntry(output_frame, width=200, font=ctk.CTkFont(size=16), fg_color="#e8f5e9")
        self.output_entry.pack(side="left", padx=5)

        self.output_unit = ctk.StringVar(value="千米")
        self.output_menu = ctk.CTkOptionMenu(output_frame, values=["千米"], variable=self.output_unit, width=150)
        self.output_menu.pack(side="left", padx=5)

        # 转换按钮
        btn_frame = ctk.CTkFrame(convert_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="🔄 换算",
            width=200,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.convert
        ).pack()

        # 常用换算参考
        ref_frame = ctk.CTkFrame(self)
        ref_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(ref_frame, text="📋 常用换算参考：", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.ref_text = ctk.CTkTextbox(ref_frame, height=120)
        self.ref_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 初始化
        self.on_category_change("长度")

    def get_units(self, category):
        """获取对应类别的单位列表"""
        units = {
            "长度": ["毫米", "厘米", "分米", "米", "千米", "英寸", "英尺", "码", "英里"],
            "重量": ["毫克", "克", "千克", "吨", "盎司", "磅", "斤", "两"],
            "面积": ["平方毫米", "平方厘米", "平方分米", "平方米", "平方千米", "公顷", "亩", "平方英尺", "平方英里"],
            "体积": ["毫升", "升", "立方米", "立方厘米", "加仑(美)", "加仑(英)", "立方英尺", "立方英寸"],
            "温度": ["摄氏度(°C)", "华氏度(°F)", "开尔文(K)"],
            "时间": ["毫秒", "秒", "分钟", "小时", "天", "周", "月(30天)", "年(365天)"],
            "速度": ["米/秒", "千米/时", "英里/时", "节", "马赫", "光速"],
            "数据存储": ["比特(bit)", "字节(B)", "千字节(KB)", "兆字节(MB)", "吉字节(GB)", "太字节(TB)", "拍字节(PB)"]
        }
        return units.get(category, [])

    def get_reference(self, category):
        """获取常用换算参考"""
        refs = {
            "长度": "1 米 = 100 厘米 = 3.28 英尺\n1 千米 = 0.62 英里\n1 英寸 = 2.54 厘米\n1 里 = 500 米",
            "重量": "1 千克 = 1000 克 = 2.20 磅 = 2 斤\n1 斤 = 500 克 = 10 两\n1 磅 = 16 盎司 ≈ 0.45 千克",
            "面积": "1 平方米 = 100 平方分米 = 10.76 平方英尺\n1 平方千米 = 100 公顷 = 1500 亩\n1 亩 ≈ 666.67 平方米",
            "体积": "1 升 = 1000 毫升 = 0.001 立方米\n1 加仑(美) ≈ 3.785 升\n1 加仑(英) ≈ 4.546 升",
            "温度": "0°C = 32°F = 273.15K\n100°C = 212°F = 373.15K\n体温正常：36.5°C ~ 37.2°C",
            "时间": "1 小时 = 60 分钟 = 3600 秒\n1 天 = 24 小时 = 1440 分钟\n1 年 ≈ 365 天 = 8760 小时",
            "速度": "1 米/秒 = 3.6 千米/时\n1 英里/时 ≈ 1.609 千米/时\n1 节 ≈ 1.852 千米/时\n光速 ≈ 3×10⁸ 米/秒",
            "数据存储": "1 字节 = 8 比特\n1 KB = 1024 B\n1 MB = 1024 KB\n1 GB = 1024 MB\n1 TB = 1024 GB"
        }
        return refs.get(category, "")

    def on_category_change(self, category):
        """类别改变时更新单位选项"""
        units = self.get_units(category)

        # 更新下拉菜单
        self.input_menu.configure(values=units)
        self.output_menu.configure(values=units)

        # 设置默认值
        if len(units) >= 2:
            self.input_unit.set(units[0])
            self.output_unit.set(units[1] if len(units) > 1 else units[0])

        # 更新参考
        self.ref_text.delete("1.0", "end")
        self.ref_text.insert("end", self.get_reference(category))

    def swap_units(self):
        """交换输入输出单位"""
        temp = self.input_unit.get()
        self.input_unit.set(self.output_unit.get())
        self.output_unit.set(temp)

        # 同时交换数值
        input_val = self.input_entry.get()
        output_val = self.output_entry.get()
        if output_val:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, output_val)

    def convert(self):
        """执行换算"""
        try:
            value = float(self.input_entry.get())
        except ValueError:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, "请输入数字")
            return

        category = self.category_var.get()
        from_unit = self.input_unit.get()
        to_unit = self.output_unit.get()

        try:
            result = self.do_convert(value, from_unit, to_unit, category)
            self.output_entry.delete(0, "end")

            # 格式化结果
            if abs(result) >= 1e6 or (abs(result) < 0.0001 and result != 0):
                self.output_entry.insert(0, f"{result:.6e}")
            else:
                self.output_entry.insert(0, f"{result:.6g}")

        except Exception as e:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, f"错误: {str(e)}")

    def do_convert(self, value, from_unit, to_unit, category):
        """实际换算逻辑"""

        # 转换为基准单位，再转换为目标单位
        if category == "长度":
            # 基准：米
            to_meter = {
                "毫米": 0.001, "厘米": 0.01, "分米": 0.1, "米": 1, "千米": 1000,
                "英寸": 0.0254, "英尺": 0.3048, "码": 0.9144, "英里": 1609.344
            }
            return value * to_meter[from_unit] / to_meter[to_unit]

        elif category == "重量":
            # 基准：克
            to_gram = {
                "毫克": 0.001, "克": 1, "千克": 1000, "吨": 1000000,
                "盎司": 28.3495, "磅": 453.592, "斤": 500, "两": 50
            }
            return value * to_gram[from_unit] / to_gram[to_unit]

        elif category == "面积":
            # 基准：平方米
            to_sqm = {
                "平方毫米": 0.000001, "平方厘米": 0.0001, "平方分米": 0.01,
                "平方米": 1, "平方千米": 1000000, "公顷": 10000,
                "亩": 666.6667, "平方英尺": 0.092903, "平方英里": 2589988.11
            }
            return value * to_sqm[from_unit] / to_sqm[to_unit]

        elif category == "体积":
            # 基准：升
            to_liter = {
                "毫升": 0.001, "升": 1, "立方米": 1000, "立方厘米": 0.001,
                "加仑(美)": 3.78541, "加仑(英)": 4.54609,
                "立方英尺": 28.3168, "立方英寸": 0.0163871
            }
            return value * to_liter[from_unit] / to_liter[to_unit]

        elif category == "温度":
            # 温度比较特殊，不能直接比例换算
            if from_unit == to_unit:
                return value

            # 先转成摄氏度
            if from_unit == "摄氏度(°C)":
                celsius = value
            elif from_unit == "华氏度(°F)":
                celsius = (value - 32) * 5 / 9
            elif from_unit == "开尔文(K)":
                celsius = value - 273.15
            else:
                raise ValueError("未知温度单位")

            # 再转成目标单位
            if to_unit == "摄氏度(°C)":
                return celsius
            elif to_unit == "华氏度(°F)":
                return celsius * 9 / 5 + 32
            elif to_unit == "开尔文(K)":
                return celsius + 273.15
            else:
                raise ValueError("未知温度单位")

        elif category == "时间":
            # 基准：秒
            to_second = {
                "毫秒": 0.001, "秒": 1, "分钟": 60, "小时": 3600,
                "天": 86400, "周": 604800, "月(30天)": 2592000, "年(365天)": 31536000
            }
            return value * to_second[from_unit] / to_second[to_unit]

        elif category == "速度":
            # 基准：米/秒
            to_mps = {
                "米/秒": 1, "千米/时": 0.277778, "英里/时": 0.44704,
                "节": 0.514444, "马赫": 340.29, "光速": 299792458
            }
            return value * to_mps[from_unit] / to_mps[to_unit]

        elif category == "数据存储":
            # 基准：字节
            to_byte = {
                "比特(bit)": 0.125, "字节(B)": 1, "千字节(KB)": 1024,
                "兆字节(MB)": 1024 * 1024, "吉字节(GB)": 1024 * 1024 * 1024,
                "太字节(TB)": 1024 ** 4, "拍字节(PB)": 1024 ** 5
            }
            return value * to_byte[from_unit] / to_byte[to_unit]

        else:
            raise ValueError("未知换算类别")
