import { writeFileSync } from 'fs'

const data = [
  // ===== 物理学 (25) =====
  { title: "量子纠缠在室温环境下的稳定性研究", category: "物理学", description: "探索在高温环境下维持量子纠缠态的方法与机制", keywords: ["量子纠缠","退相干","室温超导"], difficulty: "hard", source: "science125" },
  { title: "暗物质粒子直接探测的新方法", category: "物理学", description: "设计新型探测器以提高弱相互作用大质量粒子的探测灵敏度", keywords: ["暗物质","WIMP","粒子探测"], difficulty: "hard", source: "science125" },
  { title: "拓扑绝缘体表面态的输运特性", category: "物理学", description: "研究拓扑绝缘体表面电子的无耗散输运行为", keywords: ["拓扑绝缘体","表面态","自旋轨道耦合"], difficulty: "hard", source: "science125" },
  { title: "引力波信号中的黑洞合并参数估计", category: "物理学", description: "利用贝叶斯推断从LIGO数据中提取黑洞质量和自旋", keywords: ["引力波","黑洞合并","LIGO"], difficulty: "hard", source: "science125" },
  { title: "高温超导机制的铜氧化物研究", category: "物理学", description: "探究铜基超导体中配对对称性与赝能隙的关系", keywords: ["高温超导","铜氧化物","d波配对"], difficulty: "hard", source: "science125" },
  { title: "光子晶体光纤中的非线性效应", category: "物理学", description: "分析微结构光纤中超连续谱产生的物理机制", keywords: ["光子晶体","非线性光学","超连续谱"], difficulty: "medium", source: "science125" },
  { title: "冷原子玻色-爱因斯坦凝聚体的涡旋动力学", category: "物理学", description: "研究BEC中量子涡旋的形成、演化与衰变", keywords: ["BEC","量子涡旋","超流"], difficulty: "hard", source: "science125" },
  { title: "等离子体湍流中的能量级联机制", category: "物理学", description: "数值模拟托卡马克等离子体中湍流输运过程", keywords: ["等离子体","湍流","核聚变"], difficulty: "hard", source: "science125" },
  { title: "二维材料异质结的光电响应", category: "物理学", description: "研究MoS2/石墨烯异质结中的载流子分离效率", keywords: ["二维材料","异质结","光电探测"], difficulty: "medium", source: "science125" },
  { title: "中微子振荡参数的精确测量", category: "物理学", description: "利用反应堆中微子实验测定混合角θ13", keywords: ["中微子","振荡","CP破坏"], difficulty: "hard", source: "science125" },
  { title: "超冷费米气体中的BCS-BEC交叉", category: "物理学", description: "通过Feshbach共振调控研究强关联费米系统", keywords: ["费米气体","BCS-BEC","Feshbach共振"], difficulty: "hard", source: "science125" },
  { title: "钙钛矿太阳能电池中的离子迁移效应", category: "物理学", description: "揭示卤化物钙钛矿中离子迁移对器件稳定性的影响", keywords: ["钙钛矿","离子迁移","光伏"], difficulty: "medium", source: "science125" },
  { title: "量子计算中的纠错码优化", category: "物理学", description: "设计低开销的表面码解码算法", keywords: ["量子纠错","表面码","容错计算"], difficulty: "hard", source: "science125" },
  { title: "声学超材料的负折射现象", category: "物理学", description: "实现声波频段的双负介质与亚波长聚焦", keywords: ["声学超材料","负折射","声聚焦"], difficulty: "medium", source: "science125" },
  { title: "宇宙微波背景辐射中的B模偏振", category: "物理学", description: "搜寻原初引力波在CMB中留下的印记", keywords: ["CMB","B模偏振","暴胀"], difficulty: "hard", source: "science125" },
  { title: "自旋电子学中的自旋霍尔效应", category: "物理学", description: "研究重金属/铁磁双层结构中自旋流的产生与检测", keywords: ["自旋电子学","自旋霍尔","自旋流"], difficulty: "medium", source: "science125" },
  { title: "激光等离子体加速器中的电子束品质控制", category: "物理学", description: "优化尾场加速中电子束的能量展宽与发散角", keywords: ["激光加速","尾场","电子束"], difficulty: "hard", source: "science125" },
  { title: "磁性斯格明子的电流驱动运动", category: "物理学", description: "研究手性磁结构中拓扑保护的纳米磁畴壁动力学", keywords: ["斯格明子","自旋转移矩","拓扑磁结构"], difficulty: "hard", source: "science125" },
  { title: "时间晶体的实验实现与表征", category: "物理学", description: "在囚禁离子系统中观测离散时间平移对称性破缺", keywords: ["时间晶体","对称性破缺","非平衡态"], difficulty: "hard", source: "science125" },
  { title: "量子热机的效率极限", category: "物理学", description: "研究有限尺寸量子系统作为工作介质时的热力学循环", keywords: ["量子热机","卡诺效率","量子热力学"], difficulty: "medium", source: "science125" },
  { title: "超快光谱学中的阿秒脉冲产生", category: "物理学", description: "利用高次谐波产生技术获得阿秒时间分辨率", keywords: ["阿秒脉冲","高次谐波","超快光学"], difficulty: "hard", source: "science125" },
  { title: "拓扑量子计算中的马约拉纳零能模", category: "物理学", description: "在半导体-超导体纳米线中寻找Majorana费米子", keywords: ["马约拉纳","拓扑量子计算","纳米线"], difficulty: "hard", source: "science125" },
  { title: "复杂网络中的同步转变临界现象", category: "物理学", description: "研究Kuramoto模型在无标度网络上的爆炸同步", keywords: ["复杂网络","同步","相变"], difficulty: "medium", source: "science125" },
  { title: "软物质中的活性流体自组织", category: "物理学", description: "探索细菌悬浮液和人工微泳体的集体运动模式", keywords: ["活性物质","自组织","生物流体"], difficulty: "medium", source: "science125" },
  { title: "量子模拟器中的多体局域化", category: "物理学", description: "利用光晶格中的超冷原子验证MBL相的存在", keywords: ["多体局域化","量子模拟","无序系统"], difficulty: "hard", source: "science125" },

  // ===== 化学 (20) =====
  { title: "金属有机框架材料的气体分离性能", category: "化学", description: "设计高选择性MOF用于CO2/N2混合气分离", keywords: ["MOF","气体分离","碳捕集"], difficulty: "medium", source: "science125" },
  { title: "单原子催化剂的活性位点表征", category: "化学", description: "利用XAFS和STEM确定Pt单原子的配位环境", keywords: ["单原子催化","XAFS","电催化"], difficulty: "hard", source: "science125" },
  { title: "锂硫电池中穿梭效应的抑制策略", category: "化学", description: "开发功能性隔膜修饰层以锚定多硫化物", keywords: ["锂硫电池","穿梭效应","储能"], difficulty: "medium", source: "science125" },
  { title: "CRISPR-Cas9基因编辑的脱靶效应分析", category: "化学", description: "全基因组测序评估Cas9核酸酶的非特异性切割", keywords: ["CRISPR","基因编辑","脱靶"], difficulty: "medium", source: "science125" },
  { title: "共价有机框架的光催化水分解", category: "化学", description: "构建可见光响应的COF用于高效产氢", keywords: ["COF","光催化","水分解"], difficulty: "hard", source: "science125" },
  { title: "固态电解质界面的形成机理", category: "化学", description: "原位表征锂电池SEI膜的组分与结构演化", keywords: ["SEI","固态电解质","锂电池"], difficulty: "hard", source: "science125" },
  { title: "手性分子的不对称合成新方法", category: "化学", description: "发展有机小分子催化的对映选择性Aldol反应", keywords: ["不对称合成","手性","有机催化"], difficulty: "medium", source: "science125" },
  { title: "电化学CO2还原为多碳产物", category: "化学", description: "铜基催化剂上C-C偶联机制的原位光谱研究", keywords: ["CO2还原","电催化","C-C偶联"], difficulty: "hard", source: "science125" },
  { title: "蛋白质折叠中间态的捕获与表征", category: "化学", description: "利用停流荧光和NMR研究快速折叠蛋白的路径", keywords: ["蛋白质折叠","中间态","生物物理"], difficulty: "hard", source: "science125" },
  { title: "自修复高分子材料的动态键设计", category: "化学", description: "基于Diels-Alder可逆反应构建热响应自愈合聚合物", keywords: ["自修复","动态共价键","高分子"], difficulty: "medium", source: "science125" },
  { title: "纳米酶的催化活性与选择性调控", category: "化学", description: "通过尺寸和形貌工程调节CeO2纳米颗粒的类酶活性", keywords: ["纳米酶","CeO2","仿生催化"], difficulty: "medium", source: "science125" },
  { title: "全固态钠离子电池的界面兼容性", category: "化学", description: "研究硫化物电解质与正极材料的化学/电化学稳定性", keywords: ["钠离子电池","固态电解质","界面"], difficulty: "hard", source: "science125" },
  { title: "超分子组装体的刺激响应行为", category: "化学", description: "设计pH/光双响应的柱芳烃主客体复合物", keywords: ["超分子","刺激响应","主客体化学"], difficulty: "medium", source: "science125" },
  { title: "绿色溶剂替代传统有机溶剂的研究", category: "化学", description: "评估深共晶溶剂在有机合成中的适用性与回收率", keywords: ["绿色化学","深共晶溶剂","可持续"], difficulty: "easy", source: "science125" },
  { title: "钙钛矿量子点的发光稳定性提升", category: "化学", description: "表面钝化策略改善CsPbBr3 QD的水氧稳定性", keywords: ["量子点","钙钛矿","LED"], difficulty: "medium", source: "science125" },
  { title: "酶促反应的定向进化与理性设计", category: "化学", description: "结合机器学习预测突变体活性加速酶工程", keywords: ["定向进化","酶工程","机器学习"], difficulty: "hard", source: "science125" },
  { title: "多孔碳材料的孔结构精准调控", category: "化学", description: "模板法制备分级多孔碳用于超级电容器", keywords: ["多孔碳","超级电容器","储能"], difficulty: "medium", source: "science125" },
  { title: "DNA纳米结构的程序化自组装", category: "化学", description: "利用DNA折纸术构建三维功能纳米器件", keywords: ["DNA纳米技术","自组装","纳米器件"], difficulty: "hard", source: "science125" },
  { title: "光致变色分子的疲劳抗性改进", category: "化学", description: "分子工程提高二芳基乙烯类化合物的光循环次数", keywords: ["光致变色","分子开关","光疲劳"], difficulty: "medium", source: "science125" },
  { title: "电催化氮还原合成氨的机理争议", category: "化学", description: "排除质子源干扰验证真正的电化学固氮活性", keywords: ["氮还原","电催化","合成氨"], difficulty: "hard", source: "science125" },

  // ===== 生物学 (20) =====
  { title: "肠道微生物组与宿主免疫互作机制", category: "生物学", description: "解析特定菌群代谢物对Treg细胞分化的调控", keywords: ["肠道菌群","免疫","代谢物"], difficulty: "hard", source: "science125" },
  { title: "表观遗传记忆在有丝分裂中的传递", category: "生物学", description: "追踪组蛋白修饰标记在DNA复制后的重建过程", keywords: ["表观遗传","组蛋白","细胞分裂"], difficulty: "hard", source: "science125" },
  { title: "衰老细胞清除对器官再生的影响", category: "生物学", description: "评估senolytic药物在小鼠肝损伤模型中的疗效", keywords: ["衰老","senolytic","再生医学"], difficulty: "medium", source: "science125" },
  { title: "植物根系分泌物对土壤微生物群落的塑造", category: "生物学", description: "代谢组学分析根际微生物招募的化学信号", keywords: ["根际","植物-微生物","代谢组学"], difficulty: "medium", source: "science125" },
  { title: "长非编码RNA在神经发育中的功能", category: "生物学", description: "筛选并验证调控皮层神经元分化的lncRNA", keywords: ["lncRNA","神经发育","基因调控"], difficulty: "hard", source: "science125" },
  { title: "CAR-T细胞治疗实体瘤的微环境障碍", category: "生物学", description: "研究肿瘤相关巨噬细胞对CAR-T浸润的抑制作用", keywords: ["CAR-T","肿瘤微环境","免疫治疗"], difficulty: "hard", source: "science125" },
  { title: "海洋浮游生物对碳泵的贡献量化", category: "生物学", description: "同位素示踪法估算生物碳通量的季节变化", keywords: ["碳泵","浮游生物","海洋生态"], difficulty: "medium", source: "science125" },
  { title: "干细胞类器官培养的标准化方案", category: "生物学", description: "建立可重复的人脑类器官分化与成熟评价体系", keywords: ["类器官","干细胞","神经科学"], difficulty: "medium", source: "science125" },
  { title: "抗生素耐药基因的横向转移机制", category: "生物学", description: "追踪质粒介导的blaNDM-1在医院环境中的传播", keywords: ["耐药性","质粒","医院感染"], difficulty: "medium", source: "science125" },
  { title: "昼夜节律钟对代谢稳态的调控", category: "生物学", description: "肝脏特异性Bmal1敲除小鼠的糖脂代谢表型分析", keywords: ["生物钟","代谢","Bmal1"], difficulty: "medium", source: "science125" },
  { title: "珊瑚白化事件中共生藻的热适应机制", category: "生物学", description: "比较不同虫黄藻品系的热耐受转录组差异", keywords: ["珊瑚白化","虫黄藻","气候变化"], difficulty: "medium", source: "science125" },
  { title: "空间转录组学揭示肿瘤异质性", category: "生物学", description: "利用Visium平台绘制乳腺癌的空间基因表达图谱", keywords: ["空间转录组","肿瘤异质性","单细胞"], difficulty: "hard", source: "science125" },
  { title: "昆虫导航中的地标学习与路径整合", category: "生物学", description: "蜜蜂蘑菇体中视觉记忆编码的神经环路解析", keywords: ["昆虫导航","蘑菇体","神经环路"], difficulty: "hard", source: "science125" },
  { title: "端粒长度与细胞衰老的因果关系验证", category: "生物学", description: "端粒酶过表达对早衰综合征小鼠寿命的影响", keywords: ["端粒","衰老","端粒酶"], difficulty: "medium", source: "science125" },
  { title: "合成生物学底盘细胞的代谢负担优化", category: "生物学", description: "动态调控外源通路表达以减少生长缺陷", keywords: ["合成生物学","代谢负担","基因线路"], difficulty: "hard", source: "science125" },
  { title: "深海热液口化能自养菌的能量代谢", category: "生物学", description: "宏基因组组装揭示氢氧化古菌的碳固定途径", keywords: ["深海","化能自养","宏基因组"], difficulty: "hard", source: "science125" },
  { title: "mRNA疫苗的递送载体优化", category: "生物学", description: "脂质纳米颗粒组成对肌肉注射后转染效率的影响", keywords: ["mRNA疫苗","LNP","药物递送"], difficulty: "medium", source: "science125" },
  { title: "植物抗病小RNA的系统性信号传导", category: "生物学", description: "嫁接实验验证siRNA在砧木-接穗间的移动", keywords: ["小RNA","植物免疫","系统性信号"], difficulty: "medium", source: "science125" },
  { title: "大脑淋巴系统在阿尔茨海默病中的作用", category: "生物学", description: "评估glymphatic清除功能障碍与Aβ沉积的关系", keywords: ["glymphatic","阿尔茨海默","Aβ"], difficulty: "hard", source: "science125" },
  { title: "极端嗜盐菌的渗透压适应策略", category: "生物学", description: "蛋白质组学分析Halobacterium在高盐条件下的应答", keywords: ["嗜盐菌","渗透压","极端微生物"], difficulty: "medium", source: "science125" },

  // ===== 计算机科学 (20) =====
  { title: "大语言模型的幻觉问题缓解方法", category: "计算机科学", description: "检索增强生成与事实核查模块的联合训练", keywords: ["LLM","幻觉","RAG"], difficulty: "hard", source: "science125" },
  { title: "联邦学习中的差分隐私保护", category: "计算机科学", description: "在保证ε-差分隐私前提下优化模型收敛速度", keywords: ["联邦学习","差分隐私","隐私计算"], difficulty: "hard", source: "science125" },
  { title: "图神经网络的可解释性研究", category: "计算机科学", description: "开发GNNExplainer的子图级归因方法", keywords: ["GNN","可解释AI","子图归因"], difficulty: "hard", source: "science125" },
  { title: "强化学习在机器人操控中的Sim-to-Real迁移", category: "计算机科学", description: "域随机化策略缩小仿真与现实的性能差距", keywords: ["强化学习","Sim-to-Real","机器人"], difficulty: "hard", source: "science125" },
  { title: "代码生成的形式化验证方法", category: "计算机科学", description: "将LLM生成代码与Coq证明助手集成以确保正确性", keywords: ["代码生成","形式化验证","LLM"], difficulty: "hard", source: "science125" },
  { title: "边缘计算中的任务卸载决策优化", category: "计算机科学", description: "多智能体深度强化学习实现动态资源分配", keywords: ["边缘计算","任务卸载","MARL"], difficulty: "medium", source: "science125" },
  { title: "对抗样本的鲁棒性认证", category: "计算机科学", description: "基于随机平滑的ℓ2范数确定性鲁棒半径计算", keywords: ["对抗鲁棒性","随机平滑","安全AI"], difficulty: "hard", source: "science125" },
  { title: "知识图谱补全中的关系推理", category: "计算机科学", description: "结合规则学习与嵌入表示的混合推理框架", keywords: ["知识图谱","链接预测","神经符号"], difficulty: "medium", source: "science125" },
  { title: "编译器自动调优的机器学习方法", category: "计算机科学", description: "贝叶斯优化搜索GCC/LLVM编译选项空间", keywords: ["编译器","自动调优","贝叶斯优化"], difficulty: "medium", source: "science125" },
  { title: "视频理解中的时序建模瓶颈", category: "计算机科学", description: "评估Transformer与状态空间模型在长视频上的效率", keywords: ["视频理解","时序建模","SSM"], difficulty: "medium", source: "science125" },
  { title: "区块链共识协议的安全性形式化分析", category: "计算机科学", description: "使用TLA+验证PoS协议的活性与安全属性", keywords: ["区块链","形式化验证","共识协议"], difficulty: "hard", source: "science125" },
  { title: "自然语言处理中的偏见检测与消除", category: "计算机科学", description: "构建多维度偏见基准测试集并提出去偏训练策略", keywords: ["NLP偏见","公平性","基准测试"], difficulty: "medium", source: "science125" },
  { title: "神经架构搜索的效率提升", category: "计算机科学", description: "权重共享与早停策略降低NAS的计算成本", keywords: ["NAS","权重共享","AutoML"], difficulty: "medium", source: "science125" },
  { title: "分布式系统中的拜占庭容错新协议", category: "计算机科学", description: "设计异步网络下最优消息复杂度的BFT共识", keywords: ["BFT","分布式共识","异步网络"], difficulty: "hard", source: "science125" },
  { title: "多模态学习的跨模态对齐", category: "计算机科学", description: "对比学习框架下图文匹配的细粒度语义对齐", keywords: ["多模态","对比学习","CLIP"], difficulty: "medium", source: "science125" },
  { title: "软件测试中的模糊测试覆盖率引导", category: "计算机科学", description: "基于程序路径敏感度的自适应种子选择策略", keywords: ["模糊测试","覆盖率","安全测试"], difficulty: "medium", source: "science125" },
  { title: "因果推断在观察性研究中的应用", category: "计算机科学", description: "双重机器学习方法估计异质性处理效应", keywords: ["因果推断","DML","观察性研究"], difficulty: "hard", source: "science125" },
  { title: "低功耗AI芯片的量化感知训练", category: "计算机科学", description: "INT4量化下保持CNN精度的梯度补偿方法", keywords: ["模型量化","QAT","AI芯片"], difficulty: "medium", source: "science125" },
  { title: "程序合成中的归纳编程方法", category: "计算机科学", description: "版本空间代数与LLM引导的候选程序枚举", keywords: ["程序合成","归纳编程","LLM"], difficulty: "hard", source: "science125" },
  { title: "推荐系统中的冷启动问题解决", category: "计算机科学", description: "元学习框架实现新用户少样本偏好建模", keywords: ["推荐系统","冷启动","元学习"], difficulty: "medium", source: "science125" },

  // ===== 地球科学 (15) =====
  { title: "青藏高原隆升对亚洲季风的影响", category: "地球科学", description: "气候模式模拟不同地形高度下的降水格局变化", keywords: ["青藏高原","季风","古气候"], difficulty: "hard", source: "science125" },
  { title: "深海稀土元素的富集机制", category: "地球科学", description: "太平洋黏土沉积物中REY的吸附-解吸动力学", keywords: ["深海稀土","黏土矿物","资源评价"], difficulty: "medium", source: "science125" },
  { title: "冰川消融对海平面上升的贡献评估", category: "地球科学", description: "GRACE卫星重力数据反演格陵兰冰盖质量损失", keywords: ["冰川","海平面","GRACE"], difficulty: "medium", source: "science125" },
  { title: "城市热岛效应的遥感监测与缓解", category: "地球科学", description: "Landsat热红外数据反演地表温度时空分布", keywords: ["热岛效应","遥感","城市气候"], difficulty: "easy", source: "science125" },
  { title: "地震预警系统的误报率优化", category: "地球科学", description: "机器学习分类器区分真实地震与噪声触发", keywords: ["地震预警","机器学习","早期预警"], difficulty: "medium", source: "science125" },
  { title: "永久冻土融化释放温室气体的通量估算", category: "地球科学", description: "涡度协方差法测量西伯利亚苔原CH4排放", keywords: ["冻土","温室气体","碳循环"], difficulty: "medium", source: "science125" },
  { title: "板块俯冲带深部碳循环", category: "地球科学", description: "变质脱碳反应对火山弧CO2通量的约束", keywords: ["俯冲带","碳循环","变质作用"], difficulty: "hard", source: "science125" },
  { title: "海洋酸化对钙化生物的影响", category: "地球科学", description: "实验室模拟未来pH条件下翼足类壳体溶解速率", keywords: ["海洋酸化","钙化生物","pH"], difficulty: "medium", source: "science125" },
  { title: "古地磁数据约束大陆重建", category: "地球科学", description: "冈瓦纳大陆裂解过程中印度板块的运动轨迹", keywords: ["古地磁","板块运动","冈瓦纳"], difficulty: "hard", source: "science125" },
  { title: "大气气溶胶对云微物理的影响", category: "地球科学", description: "飞机观测验证间接效应在暖云中的显著性", keywords: ["气溶胶","云微物理","间接效应"], difficulty: "medium", source: "science125" },
  { title: "地下水污染的自然衰减评估", category: "地球科学", description: "同位素示踪法量化氯代烃的生物降解速率", keywords: ["地下水","自然衰减","生物修复"], difficulty: "medium", source: "science125" },
  { title: "火星表面液态水活动的地质证据", category: "地球科学", description: "HiRISE影像中季节性斜坡纹线的成因争议", keywords: ["火星","液态水","行星地质"], difficulty: "hard", source: "science125" },
  { title: "河流三角洲对海平面上升的响应", category: "地球科学", description: "沉积物收支模型预测密西西比三角洲的未来演变", keywords: ["三角洲","海平面","沉积物"], difficulty: "medium", source: "science125" },
  { title: "火山喷发对平流层臭氧的影响", category: "地球科学", description: "皮纳图博 eruption 后臭氧化学扰动的卫星观测", keywords: ["火山","平流层","臭氧"], difficulty: "medium", source: "science125" },
  { title: "土壤有机碳的稳定化机制", category: "地球科学", description: "矿物结合态与颗粒态碳在不同土地利用下的周转", keywords: ["土壤碳","矿物结合","碳汇"], difficulty: "medium", source: "science125" },

  // ===== 数学 (15) =====
  { title: "黎曼猜想的数值验证进展", category: "数学", description: "利用Odlyzko-Schönhage算法验证前10^13个零点", keywords: ["黎曼猜想","ζ函数","数值验证"], difficulty: "hard", source: "science125" },
  { title: "偏微分方程的正则性理论", category: "数学", description: "Navier-Stokes方程三维光滑解的存在性问题", keywords: ["NS方程","正则性","千禧年问题"], difficulty: "hard", source: "science125" },
  { title: "随机矩阵理论在数据科学中的应用", category: "数学", description: "Marchenko-Pastur定律在高维协方差估计中的角色", keywords: ["随机矩阵","高维统计","谱分析"], difficulty: "hard", source: "science125" },
  { title: "代数几何中的Motivic同伦论", category: "数学", description: "Morel-Voevodsky A1同伦范畴的构造与应用", keywords: ["motivic同伦","代数几何","同伦论"], difficulty: "hard", source: "science125" },
  { title: "组合优化问题的近似算法设计", category: "数学", description: "旅行商问题的Christofides算法改进与下界分析", keywords: ["TSP","近似算法","组合优化"], difficulty: "medium", source: "science125" },
  { title: "数论中的筛法新进展", category: "数学", description: "Maynard-Tao方法在有界间隙素数问题中的应用", keywords: ["素数间隙","筛法","解析数论"], difficulty: "hard", source: "science125" },
  { title: "最优传输理论的数值方法", category: "数学", description: "Sinkhorn算法的加速与正则化参数选择", keywords: ["最优传输","Sinkhorn","Wasserstein距离"], difficulty: "medium", source: "science125" },
  { title: "遍历理论中的多重回归定理", category: "数学", description: "Furstenberg对应原理在Szemerédi定理证明中的作用", keywords: ["遍历理论","Szemerédi","组合数论"], difficulty: "hard", source: "science125" },
  { title: "拓扑数据分析的持久同调", category: "数学", description: "Vietoris-Rips复形的条形码稳定性定理", keywords: ["TDA","持久同调","拓扑"], difficulty: "medium", source: "science125" },
  { title: "有限域上代数曲线的有理点计数", category: "数学", description: "Weil猜想的证明思路与ℓ进上同调的应用", keywords: ["Weil猜想","有理点","ℓ进上同调"], difficulty: "hard", source: "science125" },
  { title: "Banach空间几何中的凸性问题", category: "数学", description: "一致凸性与Radon-Nikodym性质的等价条件", keywords: ["Banach空间","一致凸","泛函分析"], difficulty: "hard", source: "science125" },
  { title: "概率论中的浓度不等式", category: "数学", description: "McDiarmid不等式在有界差分条件下的推广", keywords: ["浓度不等式","概率论","集中现象"], difficulty: "medium", source: "science125" },
  { title: "微分几何中的Ricci流奇点分析", category: "数学", description: "Perelman熵泛函在三维流形分类中的应用", keywords: ["Ricci流","庞加莱猜想","几何分析"], difficulty: "hard", source: "science125" },
  { title: "编码理论中的LDPC码译码阈值", category: "数学", description: "密度进化分析确定正则LDPC码的BP阈值", keywords: ["LDPC","密度进化","信道编码"], difficulty: "medium", source: "science125" },
  { title: "博弈论中的机制设计与收入等价", category: "数学", description: "Myerson最优拍卖在非对称 bidder 下的扩展", keywords: ["机制设计","拍卖理论","博弈论"], difficulty: "medium", source: "science125" },

  // ===== 医学与健康 (10) =====
  { title: "阿尔茨海默病的血液生物标志物开发", category: "医学与健康", description: "血浆p-tau217作为早期诊断指标的灵敏度和特异度", keywords: ["阿尔茨海默","生物标志物","p-tau"], difficulty: "medium", source: "science125" },
  { title: "mRNA癌症疫苗的个体化新抗原设计", category: "医学与健康", description: "基于肿瘤突变谱预测HLA结合肽段并验证免疫原性", keywords: ["癌症疫苗","新抗原","个体化医疗"], difficulty: "hard", source: "science125" },
  { title: "肠道菌群移植治疗难治性C.difficile感染", category: "医学与健康", description: "随机对照试验评估FMT的临床治愈率与安全性", keywords: ["FMT","艰难梭菌","微生态"], difficulty: "medium", source: "science125" },
  { title: "GLP-1受体激动剂的心血管保护作用", category: "医学与健康", description: "大规模临床试验meta分析评估心血管终点事件", keywords: ["GLP-1","心血管","糖尿病"], difficulty: "medium", source: "science125" },
  { title: "液体活检在肺癌早筛中的临床应用", category: "医学与健康", description: "ctDNA甲基化panel的灵敏度与假阳性率评估", keywords: ["液体活检","ctDNA","肺癌筛查"], difficulty: "medium", source: "science125" },
  { title: "睡眠剥夺对认知功能的急性影响", category: "医学与健康", description: "fMRI研究24小时不眠对工作记忆网络的扰动", keywords: ["睡眠剥夺","认知","fMRI"], difficulty: "easy", source: "science125" },
  { title: "基因治疗遗传性视网膜疾病的长期随访", category: "医学与健康", description: "Luxturna治疗后5年视力维持情况与安全性", keywords: ["基因治疗","视网膜","遗传病"], difficulty: "medium", source: "science125" },
  { title: "人工智能辅助病理诊断的准确性验证", category: "医学与健康", description: "深度学习模型在乳腺癌淋巴结转移检测中的表现", keywords: ["AI病理","深度学习","乳腺癌"], difficulty: "medium", source: "science125" },
  { title: "间歇性禁食对代谢综合征的干预效果", category: "医学与健康", description: "16:8限时进食对胰岛素抵抗和血脂的RCT研究", keywords: ["间歇性禁食","代谢综合征","营养学"], difficulty: "easy", source: "science125" },
  { title: "抗抑郁药物的安慰剂效应量化", category: "医学与健康", description: "meta回归分析SSRI试验中安慰剂组的HAM-D变化", keywords: ["安慰剂效应","抗抑郁","meta分析"], difficulty: "medium", source: "science125" },
]

const ts = \// Auto-generated Science 125 research topics
// Generated at \

export interface Science125Item {
  title: string
  category: string
  description: string
  keywords: string[]
  difficulty: string
  source: string
}

export const SCIENCE_125_DATA: Science125Item[] = \
\

writeFileSync('src/data/science125.ts', ts, 'utf-8')
console.log(\Generated science125.ts with \ items\)
