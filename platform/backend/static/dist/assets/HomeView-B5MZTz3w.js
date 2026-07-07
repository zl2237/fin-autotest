import{d as K,c as Q,a,b as l,w as n,t as E,j as d,n as J,k as x,g as c,i as w,r as i,o as P,l as S,m as X,p as G,q as Z,s as A,v as T,x as ee,y as le,z as N,A as ae,B as ne,C as te,D as re,h as oe,F as de,E as h,u as se,_ as ie}from"./index-BYgyK6fo.js";import{r as C}from"./request-DaYtLPIS.js";import{u as ce}from"./auth-B5Tlwb9L.js";const ue={class:"page"},pe={class:"sidebar-user"},_e={class:"username"},ve={class:"main"},me={class:"manual-container"},fe={class:"manual-section"},be={class:"manual-section"},ke={class:"manual-section"},ye=K({__name:"HomeView",setup(ge){const I=se(),u=ce(),v=w(!1),L=[{layer:"测试框架",tech:"pytest",version:">=7.4.0"},{layer:"HTTP 客户端",tech:"requests",version:">=2.31.0"},{layer:"日志记录",tech:"loguru",version:">=0.7.2"},{layer:"YAML 配置",tech:"PyYAML",version:">=6.0"},{layer:"后端框架",tech:"Flask",version:">=3.0.0"},{layer:"数据库",tech:"SQLite",version:"3.x（无需额外服务）"},{layer:"前端框架",tech:"Vue 3 + Vite",version:"^3.4 / ^5.0"},{layer:"UI 组件库",tech:"Element Plus",version:"^2.4.0"}],M=[{field:"名称",desc:"如 uat、sit、prod"},{field:"API 地址",desc:"被测系统域名，如 https://xxx.com"},{field:"账号 / 密码",desc:"登录凭据"},{field:"Token 字段",desc:"响应中 token 路径，默认 data.token"},{field:"默认",desc:"是否设为默认环境"}],R=[{link:"order1",stage:"新建",link2:"order_pay_receive1",stage2:"发起应付对账批次"},{link:"order2",stage:"分发",link2:"order_pay_receive2",stage2:"确认应付对账"},{link:"order3",stage:"暂存",link2:"order_pay_receive3",stage2:"发起应付开票批次申请"},{link:"order4",stage:"提交",link2:"order_pay_receive4",stage2:"应付发票上传与登记"},{link:"order5",stage:"生成子订单",link2:"order_pay_receive5",stage2:"发起付款需求"},{link:"order6",stage:"录费用",link2:"order_pay_receive6",stage2:"审核生成付款单"},{link:"order7",stage:"资产推送审批",link2:"order_pay_receive7",stage2:"付款单核销"},{link:"order8",stage:"订单锁定审批",link2:"order_pay_receive8",stage2:"发起应收对账批次"},{link:"order9",stage:"未放款开票申请审批",link2:"order_pay_receive9",stage2:"确认应收对账"},{link:"order10",stage:"供应商垫付申请审批",link2:"order_pay_receive10",stage2:"发起应收开票批次审批"},{link:"order11",stage:"生成费用通知单",link2:"order_pay_receive11",stage2:"审核生成开票申请"},{link:"order12",stage:"生成费用确认单",link2:"order_pay_receive12",stage2:"发票上传与登记"},{link:"order_pay_receive13",stage:"应收核销",link2:"order_receive_pay1",stage2:"发起应收对账批次"},{link:"order_receive_pay2",stage:"确认应收对账",link2:"order_receive_pay3",stage2:"发起应收开票批次审批"},{link:"order_receive_pay4",stage:"审核生成开票申请",link2:"order_receive_pay5",stage2:"发票上传与登记"},{link:"order_receive_pay6",stage:"应收核销",link2:"order_receive_pay7",stage2:"发起应付对账批次"},{link:"order_receive_pay8",stage:"确认应付对账",link2:"order_receive_pay9",stage2:"发起应付开票批次申请"},{link:"order_receive_pay10",stage:"应付发票上传与登记",link2:"order_receive_pay11",stage2:"发起付款需求"},{link:"order_receive_pay12",stage:"审核生成付款单",link2:"order_receive_pay13",stage2:"付款单核销"},{link:"",stage:"",link2:"",stage2:""}];function D(){u.logout(),I.push({name:"Login"})}const m=w(!1),k=w(!1),t=oe({name:"",phone:"",email:"",password:"",confirmPassword:""}),O=w(!1),_=w(null);async function U(){m.value=!0,k.value=!0;try{const{data:r}=await C.get("/auth/me"),e=r==null?void 0:r.user;if(!e)throw new Error((r==null?void 0:r.message)||"获取用户信息失败");Object.assign(t,{name:e.name||"",phone:e.phone||"",email:e.email||"",password:"",confirmPassword:""}),_.value=null}catch(r){h.error((r==null?void 0:r.message)||"获取用户信息失败"),m.value=!1}finally{k.value=!1}}async function V(){const r=t.phone.trim();if(!r){_.value=null;return}O.value=!0;try{const{data:e}=await C.get("/auth/check-phone",{params:{phone:r,exclude_user_id:u.user_id}});_.value=e!=null&&e.taken?"taken":"ok"}catch{_.value=null}finally{O.value=!1}}const q=de(()=>{const r=t.name.trim().length>0,e=t.phone.trim().length>0&&/^\+?\d{6,15}$/.test(t.phone.trim()),o=!t.password||t.password===t.confirmPassword;return r&&e&&o&&_.value!=="taken"});async function z(){if(t.password&&t.password!==t.confirmPassword){h.error("两次输入的密码不一致");return}if(_.value==="taken"){h.error("手机号已存在，请更换");return}k.value=!0;try{const r={name:t.name.trim(),phone:t.phone.trim(),email:t.email.trim()};t.password.trim()&&(r.password=t.password.trim());const{data:e}=await C.put("/auth/me",r);if(!(e!=null&&e.ok))throw new Error((e==null?void 0:e.message)||"更新失败");const o=(e==null?void 0:e.user)||{};u.login(u.username,u.token,u.role,o.name,o.phone,o.email,o.user_id),h.success("个人信息已更新"),m.value=!1}catch(r){h.error((r==null?void 0:r.message)||"更新失败")}finally{k.value=!1}}return(r,e)=>{const o=i("el-icon"),B=i("el-tag"),y=i("el-button"),g=i("el-menu-item"),F=i("el-sub-menu"),H=i("el-menu"),Y=i("el-divider"),p=i("el-table-column"),W=i("el-table"),f=i("el-input"),b=i("el-form-item"),j=i("el-form"),$=i("el-dialog");return P(),Q("div",ue,[a("aside",{class:J(["sidebar",{collapsed:v.value}])},[a("button",{class:"sidebar-toggle",onClick:e[0]||(e[0]=s=>v.value=!v.value)},[l(o,null,{default:n(()=>[v.value?(P(),S(d(G),{key:1})):(P(),S(d(X),{key:0}))]),_:1})]),e[15]||(e[15]=a("div",{class:"sidebar-brand"},[a("svg",{class:"brand-icon",viewBox:"0 0 24 24",fill:"none"},[a("path",{d:"M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0-6v6m18-6v6",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"})]),a("span",{class:"brand-text"},"API 测试平台")],-1)),a("div",pe,[l(B,{type:"info",size:"small",effect:"plain"},{default:n(()=>[...e[8]||(e[8]=[c("PR Study",-1)])]),_:1}),a("span",_e,E(d(u).name||d(u).username),1),l(y,{type:"primary",plain:"",size:"small",onClick:U},{default:n(()=>[l(o,null,{default:n(()=>[l(d(Z))]),_:1}),A(a("span",null,"修改个人信息",512),[[T,!v.value]])]),_:1}),l(y,{type:"danger",plain:"",size:"small",onClick:D},{default:n(()=>[l(o,null,{default:n(()=>[l(d(ee))]),_:1}),A(a("span",null,"退出",512),[[T,!v.value]])]),_:1})]),l(H,{"default-active":r.$route.path,class:"sidebar-menu",collapse:v.value,"collapse-transition":!1,router:""},{default:n(()=>[l(g,{index:"/"},{title:n(()=>[...e[9]||(e[9]=[c("首页概览",-1)])]),default:n(()=>[l(o,null,{default:n(()=>[l(d(le))]),_:1})]),_:1}),l(F,{index:"logistics"},{title:n(()=>[l(o,null,{default:n(()=>[l(d(N))]),_:1}),e[10]||(e[10]=a("span",null,"物流系统",-1))]),default:n(()=>[l(g,{index:"/logistics/link-test"},{default:n(()=>[l(o,null,{default:n(()=>[l(d(N))]),_:1}),e[11]||(e[11]=a("span",null,"链路测试",-1))]),_:1}),l(g,{index:"/logistics/document-upload"},{default:n(()=>[l(o,null,{default:n(()=>[l(d(ae))]),_:1}),e[12]||(e[12]=a("span",null,"单证上传",-1))]),_:1}),l(g,{index:"/logistics/approval-config"},{default:n(()=>[l(o,null,{default:n(()=>[l(d(ne))]),_:1}),e[13]||(e[13]=a("span",null,"审批流配置",-1))]),_:1})]),_:1}),d(u).isAdmin?(P(),S(g,{key:0,index:"/platform/users"},{title:n(()=>[...e[14]||(e[14]=[c("用户管理",-1)])]),default:n(()=>[l(o,null,{default:n(()=>[l(d(te))]),_:1})]),_:1})):re("",!0)]),_:1},8,["default-active","collapse"])],2),a("div",ve,[a("div",me,[e[25]||(e[25]=a("h1",{class:"manual-title"},"PR Study - 项目用户手册",-1)),e[26]||(e[26]=a("p",{class:"manual-subtitle"},"接口自动化测试框架 + Web 测试平台",-1)),l(Y),e[27]||(e[27]=x('<section class="manual-section" data-v-c1cd62cb><h2 data-v-c1cd62cb>项目简介</h2><p data-v-c1cd62cb>基于 pytest + requests 的接口自动化测试框架，用于物流管理系统的全流程接口测试，覆盖从新建订单到付款单核销的 38 条链路。</p><p data-v-c1cd62cb>38 条链路按依赖顺序递增。配置与代码分离，所有业务参数均存储在 YAML，通过 <code data-v-c1cd62cb>TEST_ENV</code> 切换环境。</p></section><section class="manual-section" data-v-c1cd62cb><h2 data-v-c1cd62cb>核心能力</h2><ul data-v-c1cd62cb><li data-v-c1cd62cb>38 条链路，覆盖订单、应付、应收全流程</li><li data-v-c1cd62cb>workflows 层自动处理步骤间数据依赖（order_id、审批ID 等自动传递）</li><li data-v-c1cd62cb>所有业务配置参数集中存储于 YAML，Python 代码零硬编码</li><li data-v-c1cd62cb>Web 平台：5 张流程选择卡片、环境管理、链路过滤、循环执行、一键执行、实时日志、执行历史、用户管理</li><li data-v-c1cd62cb>data 层按环境自动加载 <code data-v-c1cd62cb>*_tidb.yaml</code> 或 <code data-v-c1cd62cb>*_pre.yaml</code>，通过 <code data-v-c1cd62cb>.env</code> 中的 <code data-v-c1cd62cb>TEST_ENV</code> 切换</li><li data-v-c1cd62cb>CI 环境自动企微机器人通知</li><li data-v-c1cd62cb>Allure 报告</li></ul></section>',2)),a("section",fe,[e[16]||(e[16]=a("h2",null,"技术栈",-1)),l(W,{data:L,stripe:"",size:"small",style:{width:"100%"}},{default:n(()=>[l(p,{prop:"layer",label:"层级",width:"120"}),l(p,{prop:"tech",label:"技术",width:"140"}),l(p,{prop:"version",label:"版本"})]),_:1})]),e[28]||(e[28]=x(`<section class="manual-section" data-v-c1cd62cb><h2 data-v-c1cd62cb>目录结构</h2><pre class="code-block" data-v-c1cd62cb>pr_study/
├── api/                            # API 层：HTTP 接口封装，按 order/receive/pay 划分域
│   ├── order/
│   ├── receive/
│   └── pay/
├── config/                         # 配置层
│   └── settings.py                 # 环境变量与全局常量
├── core/                           # 基础设施
│   └── http_client.py              # 统一 HTTP 客户端
├── data/                           # 数据层：YAML 配置 + 数据构建，按环境自动加载
│   ├── env.py
│   ├── order/
│   ├── receive/
│   └── pay/
├── utils/                          # 公共工具
│   ├── __init__.py
│   ├── generate.py                 # 测试数据生成/编码生成
│   └── logger.py                   # 日志初始化与格式化
├── testcases/                      # pytest 用例，按 order/pay_receive/receive_pay 分组
│   ├── conftest.py
│   ├── order/
│   ├── pay_receive/
│   └── receive_pay/
├── workflows/                      # 流程编排：业务链路到 steps 的调度与依赖传递
│   ├── order/
│   ├── pay/
│   ├── pay_receive_workflow.py
│   └── receive_pay_workflow.py
├── platform/                       # Web 测试平台
│   ├── backend/                    # Flask 后端：执行调度、日志、用户管理
│   └── frontend/                   # Vue 3 前端：链路选择、执行、历史、用户管理
├── .gitlab-ci.yml                  # CI 配置
├── .gitignore
├── .env.example
├── conftest.py                     # pytest 根配置、环境与 fixtures
├── notify.py                       # 企微通知
├── pytest.ini
└── requirements.txt                # Python 依赖</pre></section><section class="manual-section" data-v-c1cd62cb><h2 data-v-c1cd62cb>快速开始</h2><h3 data-v-c1cd62cb>1. 克隆项目</h3><pre class="code-block" data-v-c1cd62cb>git clone http://172.16.18.55:88/root/pr_study.git
cd pr_study</pre><h3 data-v-c1cd62cb>2. 安装依赖</h3><p data-v-c1cd62cb><strong data-v-c1cd62cb>后端（Python）：</strong></p><pre class="code-block" data-v-c1cd62cb>cd platform/backend
pip install -r requirements.txt</pre><p data-v-c1cd62cb><strong data-v-c1cd62cb>前端（Node.js）：</strong></p><pre class="code-block" data-v-c1cd62cb>cd platform/frontend
npm install</pre><h3 data-v-c1cd62cb>3. 配置环境</h3><p data-v-c1cd62cb><strong data-v-c1cd62cb>后端环境变量：</strong></p><pre class="code-block" data-v-c1cd62cb>cp platform/backend/.env.example platform/backend/.env
# 编辑 .env，填入管理员账号和被测系统配置</pre><p data-v-c1cd62cb><strong data-v-c1cd62cb>前端代理（开发模式）：</strong></p><p data-v-c1cd62cb>platform/frontend/vite.config.js 中已配置 Vite 代理到 http://localhost:5000。</p></section><section class="manual-section" data-v-c1cd62cb><h2 data-v-c1cd62cb>运行方式</h2><h3 data-v-c1cd62cb>方式一：开发模式（推荐用于本地调试）</h3><p data-v-c1cd62cb><strong data-v-c1cd62cb>终端 1 - 启动 Flask 后端：</strong></p><pre class="code-block" data-v-c1cd62cb>cd platform/backend
python run.py
# 服务运行在 http://localhost:5000</pre><p data-v-c1cd62cb><strong data-v-c1cd62cb>终端 2 - 启动 Vue 前端：</strong></p><pre class="code-block" data-v-c1cd62cb>cd platform/frontend
npm run dev
# 访问 http://localhost:3000</pre><h3 data-v-c1cd62cb>方式二：生产模式（Flask 托管构建后的静态文件）</h3><pre class="code-block" data-v-c1cd62cb># 1. 构建前端
cd platform/frontend
npm run build

# 2. 将构建产物复制到 platform/backend/static
# Linux / macOS
cp -r platform/frontend/dist/* platform/backend/static/
# Windows (PowerShell)
Copy-Item -Recurse platform/frontend/dist/* platform/backend/static/

# 3. 启动 Flask（同时服务 API + 静态页面）
cd platform/backend
python run.py</pre></section>`,3)),a("section",be,[e[17]||(e[17]=a("h2",null,"Web 平台使用",-1)),e[18]||(e[18]=a("h3",null,"1. 登录",-1)),e[19]||(e[19]=a("ul",null,[a("li",null,[c("默认手机号："),a("code",null,"13800000000")]),a("li",null,[c("默认密码："),a("code",null,"admin123")]),a("li",null,"在 .env 中修改 ADMIN_PASSWORD")],-1)),e[20]||(e[20]=a("h3",null,"2. 环境管理",-1)),e[21]||(e[21]=a("p",null,"在「环境管理」页面添加被测系统环境：",-1)),l(W,{data:M,stripe:"",size:"small",style:{width:"100%"}},{default:n(()=>[l(p,{prop:"field",label:"字段",width:"120"}),l(p,{prop:"desc",label:"说明"})]),_:1}),e[22]||(e[22]=x("<h3 data-v-c1cd62cb>3. 发起测试</h3><ol data-v-c1cd62cb><li data-v-c1cd62cb>选择流程卡片</li><li data-v-c1cd62cb>选择环境</li><li data-v-c1cd62cb>选择运行链路</li><li data-v-c1cd62cb>设置循环次数（1~100）</li><li data-v-c1cd62cb>（可选）输入费用配置 JSON</li><li data-v-c1cd62cb>点击「开始执行」</li></ol><p data-v-c1cd62cb>平台将：</p><ul data-v-c1cd62cb><li data-v-c1cd62cb>自动写入 .env 凭据</li><li data-v-c1cd62cb>在子进程中调用 pytest</li><li data-v-c1cd62cb>通过 SSE 实时推送日志到前端</li><li data-v-c1cd62cb>将执行结果存入 SQLite</li></ul><h3 data-v-c1cd62cb>4. 执行历史</h3><p data-v-c1cd62cb>查看历史执行记录，包括状态、链路、耗时、通过/失败数量。</p>",6))]),e[29]||(e[29]=a("section",{class:"manual-section"},[a("h2",null,"直接运行 pytest（命令行模式）"),a("p",null,"保留原有的 pytest 命令行能力，不依赖 Web 平台："),a("pre",{class:"code-block"},`# 配置被测系统
cp .env.example .env
# 编辑 .env 填入 BASE_URL、USERNAME、PASSWORD

# 运行
pytest -v                          # 全部
pytest -m order1                   # 仅订单链路1
pytest -m "order_pay_receive1 or order_pay_receive8"       # 多条链路
pytest -m order_pay_receive13      # 订单+应付+应收全流程
pytest -m order_receive_pay13      # 订单+应收+应付全流程`)],-1)),a("section",ke,[e[23]||(e[23]=a("h2",null,"链路一览（38 条）",-1)),l(W,{data:R,stripe:"",size:"small",style:{width:"100%"}},{default:n(()=>[l(p,{prop:"link",label:"链路",width:"120"}),l(p,{prop:"stage",label:"停止阶段"}),l(p,{prop:"link2",label:"链路",width:"120"}),l(p,{prop:"stage2",label:"停止阶段"})]),_:1}),e[24]||(e[24]=a("p",{class:"manual-note"},[c("实际链路命名："),a("code",null,"order1~order12"),c("、"),a("code",null,"order_pay_receive1~order_pay_receive13"),c("、"),a("code",null,"order_receive_pay1~order_receive_pay13"),c("。")],-1))]),e[30]||(e[30]=a("section",{class:"manual-section"},[a("h2",null,"快捷方法"),a("p",null,"OrderWorkflow 提供 run_until_xxx 系列方法："),a("pre",{class:"code-block"},`from workflows.order_workflow import OrderWorkflow

OrderWorkflow.run_until_distribute()                # order2
OrderWorkflow.run_until_stash()                    # order3
OrderWorkflow.run_until_generate_sub_order()        # order5
OrderWorkflow.run_until_record_fee(...)             # order6
OrderWorkflow.run_until_record_audit()              # order7
OrderWorkflow.run_until_order_lock()                # order8
OrderWorkflow.run_until_invoice_apply()             # order9
OrderWorkflow.run_until_supplier_advance()          # order10
OrderWorkflow.run_until_fee_notice()                # order11
OrderWorkflow.run_until_fee_confirm()               # order12
OrderWorkflow.run_until_receive_account()           # order13
OrderWorkflow.run_until_confirm_account()           # order14
OrderWorkflow.run_until_invoice_batch()             # order15
OrderWorkflow.run_until_invoice_batch_audit()      # order16
OrderWorkflow.run_until_invoice_upload()            # order17
OrderWorkflow.run_until_receive_writeoff()          # order18
OrderWorkflow.run_until_payable_account()           # order19
OrderWorkflow.run_until_confirm_payable()           # order20
OrderWorkflow.run_until_payable_invoice_apply()     # order21
OrderWorkflow.run_until_pay_demand()                # order23
OrderWorkflow.run_until_pay_demand_audit()          # order24
OrderWorkflow.run_until_pay_writeoff()              # order25`)],-1)),e[31]||(e[31]=a("section",{class:"manual-section"},[a("h2",null,"安全提示"),a("ul",null,[a("li",null,".env 文件包含敏感凭据，已加入 .gitignore"),a("li",null,"生产部署请修改 ADMIN_PASSWORD 和 SECRET_KEY"),a("li",null,"如仅内网使用，TOKEN_EXPIRE_SECONDS 可设为 0（永不过期）"),a("li",null,"建议在 Nginx 前配置 HTTPS（Let's Encrypt）")])],-1))]),l($,{modelValue:m.value,"onUpdate:modelValue":e[7]||(e[7]=s=>m.value=s),title:"修改个人信息",width:"460px","close-on-click-modal":!1},{footer:n(()=>[l(y,{onClick:e[6]||(e[6]=s=>m.value=!1)},{default:n(()=>[...e[32]||(e[32]=[c("取消",-1)])]),_:1}),l(y,{type:"primary",loading:k.value,disabled:!q.value,onClick:z},{default:n(()=>[...e[33]||(e[33]=[c("保存",-1)])]),_:1},8,["loading","disabled"])]),default:n(()=>[l(j,{model:t,"label-width":"100px"},{default:n(()=>[l(b,{label:"账号"},{default:n(()=>[l(f,{"model-value":d(u).username,disabled:""},null,8,["model-value"])]),_:1}),l(b,{label:"姓名",required:""},{default:n(()=>[l(f,{modelValue:t.name,"onUpdate:modelValue":e[1]||(e[1]=s=>t.name=s),placeholder:"请输入姓名"},null,8,["modelValue"])]),_:1}),l(b,{label:"手机号",required:""},{default:n(()=>[l(f,{modelValue:t.phone,"onUpdate:modelValue":e[2]||(e[2]=s=>t.phone=s),placeholder:"请输入手机号",onBlur:V,onChange:V},{append:n(()=>[l(y,{loading:O.value,onClick:V},{default:n(()=>[c(E(O.value?"校验中":_.value==="taken"?"已存在":_.value==="ok"?"可用":"校验"),1)]),_:1},8,["loading"])]),_:1},8,["modelValue"])]),_:1}),l(b,{label:"邮箱"},{default:n(()=>[l(f,{modelValue:t.email,"onUpdate:modelValue":e[3]||(e[3]=s=>t.email=s),placeholder:"请输入邮箱"},null,8,["modelValue"])]),_:1}),l(b,{label:"新密码"},{default:n(()=>[l(f,{modelValue:t.password,"onUpdate:modelValue":e[4]||(e[4]=s=>t.password=s),type:"password","show-password":"",placeholder:"留空不修改"},null,8,["modelValue"])]),_:1}),l(b,{label:"确认密码"},{default:n(()=>[l(f,{modelValue:t.confirmPassword,"onUpdate:modelValue":e[5]||(e[5]=s=>t.confirmPassword=s),type:"password","show-password":"",placeholder:"请再次输入密码"},null,8,["modelValue"])]),_:1})]),_:1},8,["model"])]),_:1},8,["modelValue"])])])}}}),Pe=ie(ye,[["__scopeId","data-v-c1cd62cb"]]);export{Pe as default};
