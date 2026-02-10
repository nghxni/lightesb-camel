# DataSonnet Import 导入语法完整指南

## 📚 基础语法

### 1. **基本导入**

```datasonnet
//%datasonnet 2.0
//%input payload application/json
//%output application/json

// 导入单个模块
local myModule = import 'my-module.ds';

// 使用导入的模块
myModule.someFunction(payload)
```

### 2. **导入路径规则**

#### 相对路径（推荐）
```datasonnet
// 同目录下的文件
local utils = import 'utils.ds';

// 子目录下的文件
local helpers = import 'lib/helpers.ds';

// 父目录下的文件
local common = import '../common.ds';
```

#### 绝对路径（不推荐，可移植性差）
```datasonnet
local config = import '/absolute/path/to/config.ds';
```

---

## 🎯 实际应用示例

### 示例 1: 创建通用函数库

**文件: `common-functions.ds`**
```datasonnet
//%datasonnet 2.0
//%output application/json

{
  // 格式化地址
  formatAddress: function(address) 
    address.province + address.city + address.street + " " + address.zipCode,
  
  // 格式化全名
  formatFullName: function(name)
    name.firstName + name.lastName,
  
  // 安全连接
  safeJoin: function(arr, separator)
    local filtered = [x for x in arr if x != null && x != ""];
    std.join(separator, filtered),
  
  // 计算总价
  calculateTotal: function(price, quantity)
    price * quantity
}
```

**文件: `main-transform.ds`**
```datasonnet
//%datasonnet 2.0
//%input payload application/json
//%output application/json

// 导入通用函数库
local lib = import 'common-functions.ds';

{
  customerName: lib.formatFullName(payload.customer.name),
  address: lib.formatAddress(payload.customer.address),
  items: [
    {
      name: item.name,
      total: lib.calculateTotal(item.price, item.quantity)
    }
    for item in payload.items
  ]
}
```

---

### 示例 2: 导入配置文件

**文件: `config.ds`**
```datasonnet
//%datasonnet 2.0
//%output application/json

{
  // 常量配置
  DEFAULT_CURRENCY: "CNY",
  DEFAULT_COUNTRY: "中国",
  TAX_RATE: 0.13,
  
  // 状态映射
  STATUS_MAP: {
    "1": "待支付",
    "2": "已支付",
    "3": "已发货",
    "4": "已完成",
    "5": "已取消"
  },
  
  // 业务规则
  SHIPPING_THRESHOLD: 99.00,
  FREE_SHIPPING_AMOUNT: 199.00
}
```

**文件: `order-transform.ds`**
```datasonnet
//%datasonnet 2.0
//%input payload application/json
//%output application/json

local config = import 'config.ds';

{
  orderId: payload.orderId,
  status: config.STATUS_MAP[payload.statusCode],
  currency: config.DEFAULT_CURRENCY,
  
  // 计算运费
  shipping: if payload.amount >= config.FREE_SHIPPING_AMOUNT then 0
            else if payload.amount >= config.SHIPPING_THRESHOLD then 5.00
            else 10.00,
  
  // 计算税费
  tax: payload.subtotal * config.TAX_RATE
}
```

---

### 示例 3: 多模块组合

**文件结构:**
```
PlatformHttp/v1.0.0/
├── input-transform.ds          # 主转换文件
├── lib/
│   ├── validators.ds           # 验证函数
│   ├── formatters.ds           # 格式化函数
│   └── calculators.ds          # 计算函数
└── config/
    ├── constants.ds            # 常量定义
    └── mappings.ds             # 映射配置
```

**文件: `lib/validators.ds`**
```datasonnet
//%datasonnet 2.0
//%output application/json

{
  isValidEmail: function(email)
    std.length(email) > 0 && std.findSubstr("@", email) != [],
  
  isValidPhone: function(phone)
    std.length(phone) == 11,
  
  validateRequired: function(value, fieldName)
    if value == null || value == "" then
      error "Required field '" + fieldName + "' is missing"
    else
      value
}
```

**文件: `lib/formatters.ds`**
```datasonnet
//%datasonnet 2.0
//%output application/json

{
  formatMoney: function(amount)
    "¥" + ("" + (std.floor(amount * 100) / 100)),
  
  formatDate: function(timestamp)
    // 简化示例，实际可以更复杂
    timestamp,
  
  formatPhone: function(phone)
    std.substr(phone, 0, 3) + "****" + std.substr(phone, 7, 4)
}
```

**文件: `input-transform.ds`**
```datasonnet
//%datasonnet 2.0
//%input payload application/json
//%output application/json

// 导入多个模块
local validators = import 'lib/validators.ds';
local formatters = import 'lib/formatters.ds';
local calculators = import 'lib/calculators.ds';
local constants = import 'config/constants.ds';

{
  // 使用验证器
  email: validators.validateRequired(payload.email, "email"),
  
  // 使用格式化器
  phone: formatters.formatPhone(payload.phone),
  totalAmount: formatters.formatMoney(payload.total),
  
  // 使用常量
  currency: constants.DEFAULT_CURRENCY
}
```

---

## 🔧 在 Camel 中使用 Import

### 配置 TransformUriResolver

你的项目中，`TransformUriResolver.java` 需要支持文件解析：

```java
static String resolveTransformUri(String path) {
    if ("ds".equals(ext) || "dsonnet".equals(ext)) {
        // Camel DataSonnet 会自动处理 import
        return "language:datasonnet:resource:file:" + path;
    }
    // ...
}
```

### 路径解析规则

DataSonnet 的 import 路径是相对于**主脚本文件**的位置：

```
主文件: lightesb-camel-appT/PlatformHttp/v1.0.0/input-transform.ds

import 'common.ds'        → 查找: .../v1.0.0/common.ds
import 'lib/utils.ds'     → 查找: .../v1.0.0/lib/utils.ds
import '../shared.ds'     → 查找: .../PlatformHttp/shared.ds
```

---

## 📖 高级用法

### 1. **导入后重命名**

```datasonnet
// 使用更简短的名称
local fmt = import 'formatters.ds';
local val = import 'validators.ds';

{
  email: val.validateEmail(payload.email),
  amount: fmt.formatMoney(payload.amount)
}
```

### 2. **条件导入（不支持，需要变通）**

DataSonnet 不支持条件 import，但可以：

```datasonnet
local config = if env == "prod" 
               then import 'config-prod.ds'
               else import 'config-dev.ds';
```

**注意**: 实际上两个文件都会被加载，只是使用哪个配置。

### 3. **导入 JSON 数据文件**

```datasonnet
// 导入 JSON 配置
local mappings = import 'status-mappings.json';

{
  status: mappings[payload.statusCode]
}
```

**文件: `status-mappings.json`**
```json
{
  "1": "Pending",
  "2": "Paid",
  "3": "Shipped",
  "4": "Completed"
}
```

### 4. **递归导入**

模块可以导入其他模块：

**文件: `base.ds`**
```datasonnet
//%datasonnet 2.0
//%output application/json

{
  PI: 3.14159,
  E: 2.71828
}
```

**文件: `math.ds`**
```datasonnet
//%datasonnet 2.0
//%output application/json

local constants = import 'base.ds';

{
  circleArea: function(radius)
    constants.PI * radius * radius
}
```

**文件: `main.ds`**
```datasonnet
//%datasonnet 2.0
//%input payload application/json
//%output application/json

local math = import 'math.ds';

{
  area: math.circleArea(payload.radius)
}
```

---

## 🚀 最佳实践

### 1. **模块化设计原则**

```
✅ 好的做法:
- 每个模块单一职责
- 函数名清晰明确
- 避免循环依赖

❌ 避免:
- 一个模块包含所有功能
- 模块间相互导入（循环依赖）
- 使用全局变量
```

### 2. **文件组织结构**

```
service/v1.0.0/
├── input-transform.ds          # 主入口
├── output-transform.ds         # 输出转换
├── lib/                        # 通用库
│   ├── validators.ds
│   ├── formatters.ds
│   └── calculators.ds
├── config/                     # 配置文件
│   ├── constants.ds
│   └── mappings.json
└── models/                     # 数据模型
    ├── customer.ds
    └── order.ds
```

### 3. **函数库模板**

```datasonnet
//%datasonnet 2.0
//%output application/json

{
  // ============= 字符串处理 =============
  trim: function(str) 
    // 实现...
    str,
  
  capitalize: function(str)
    // 实现...
    str,
  
  // ============= 数组处理 =============
  unique: function(arr)
    // 实现...
    arr,
  
  flatten: function(arr)
    // 实现...
    arr,
  
  // ============= 对象处理 =============
  merge: function(obj1, obj2)
    obj1 + obj2,
  
  pick: function(obj, keys)
    // 实现...
    obj
}
```

---

## ⚠️ 常见问题

### 问题 1: 找不到导入文件

**错误信息:**
```
Error: Unable to import 'common.ds': File not found
```

**解决方案:**
1. 检查文件路径是否正确
2. 确保文件存在于指定位置
3. 使用相对路径而非绝对路径

### 问题 2: 循环依赖

**错误场景:**
```datasonnet
// a.ds 导入 b.ds
local b = import 'b.ds';

// b.ds 导入 a.ds
local a = import 'a.ds';  // 错误！循环依赖
```

**解决方案:**
- 重构代码，提取共同依赖到第三个模块

### 问题 3: 导入的函数无法访问

**错误示例:**
```datasonnet
// common.ds
function formatName(name)  // ❌ 错误：没有导出
  name.first + name.last
```

**正确示例:**
```datasonnet
// common.ds
{
  formatName: function(name)  // ✅ 正确：作为对象属性导出
    name.first + name.last
}
```

---

## 🧪 测试示例

### 测试你的导入模块

创建 `test-import.ds`:

```datasonnet
//%datasonnet 2.0
//%output application/json

local lib = import 'common-functions.ds';

// 测试导入的函数
{
  test1: lib.formatFullName({firstName: "张", lastName: "三"}),
  test2: lib.formatAddress({
    province: "北京市",
    city: "北京",
    street: "中关村大街1号",
    zipCode: "100080"
  }),
  test3: lib.calculateTotal(100, 5)
}
```

**预期输出:**
```json
{
  "test1": "张三",
  "test2": "北京市北京中关村大街1号 100080",
  "test3": 500
}
```

---

## 📝 总结

### Import 语法要点

1. **基本语法**: `local moduleName = import 'path/to/file.ds';`
2. **路径**: 相对于主脚本文件的位置
3. **导出**: 模块需要返回对象或函数
4. **使用**: `moduleName.functionName(args)`

### 优势

- ✅ 代码复用
- ✅ 模块化管理
- ✅ 易于维护
- ✅ 提高可读性

### 注意事项

- ⚠️ 避免循环依赖
- ⚠️ 使用相对路径
- ⚠️ 注意文件编码（UTF-8）
- ⚠️ 测试导入路径

---

## Java Bean 方式 —— 在路由 XML 中使用公共函数

除了在 DS 转换脚本中通过 `import` 复用公共函数，LightESB 还提供了等价的 **Java 实现**，
已通过路由加载器自动注册为 `commonFunctions` Bean，可在路由 XML 中直接调用。

### Java 类

```
com.oureman.soa.lightesb.core.util.CommonFunctions
```

注册名：`commonFunctions`（在 `EnhancedRouteLoader.injectConfigurationToContext` 中自动注入）

### 函数对照表

| DS 函数 | Java 方法 | 说明 |
|---|---|---|
| `formatAddress(address)` | `formatAddress(Map)` / `formatAddress(province, city, street, zipCode)` | 格式化地址 |
| `formatFullName(name)` | `formatFullName(Map)` / `formatFullName(firstName, lastName)` | 格式化全名 |
| `formatCategory(category)` | `formatCategory(Map)` / `formatCategory(primary, secondary, tertiary)` | 格式化类别路径 |
| `safeJoin(arr, separator)` | `safeJoin(List, separator)` | 安全连接字符串 |
| `formatSpecifications(specs)` | `formatSpecifications(Map)` | 格式化规格信息 |
| `formatWarranty(warranty)` | `formatWarranty(Map)` / `formatWarranty(type, duration)` | 格式化保修 |
| `calculateLineTotal(price, qty)` | `calculateLineTotal(price, quantity)` | 计算行总价 |
| `safeGet(obj, key, default)` | `safeGet(Map, key, defaultValue)` | 安全取值 |
| `formatAmount(amount)` | `formatAmount(amount)` | 金额保留2位小数 |
| `formatDate(dateStr)` | `formatDate(dateStr)` | 日期格式化 |
| `validateRequired(value, name)` | `validateRequired(value, fieldName)` | 验证必填字段 |

### 路由 XML 中使用示例

```xml
<routes xmlns="http://camel.apache.org/schema/spring">
    <route id="common-functions-demo">
        <from uri="undertow:http://0.0.0.0:18080/api/demo" />

        <!-- 示例1：使用 bean 调用 formatFullName -->
        <setProperty name="customerName">
            <method ref="commonFunctions" method="formatFullName(${body[firstName]}, ${body[lastName]})" />
        </setProperty>

        <!-- 示例2：使用 bean 调用 formatAmount -->
        <setProperty name="formattedAmount">
            <method ref="commonFunctions" method="formatAmount(${body[amount]})" />
        </setProperty>

        <!-- 示例3：使用 bean 调用 validateRequired -->
        <setProperty name="validatedField">
            <method ref="commonFunctions" method="validateRequired(${body[orderId]}, 'orderId')" />
        </setProperty>

        <transform>
            <simple>{
                "customerName": "${exchangeProperty.customerName}",
                "formattedAmount": "${exchangeProperty.formattedAmount}"
            }</simple>
        </transform>
    </route>
</routes>
```

### 两种方式对比

| 维度 | DS Import 方式 | Java Bean 方式 |
|---|---|---|
| 使用场景 | DataSonnet `.ds` 转换脚本内 | 路由 XML / Java Processor 中 |
| 引用方式 | `local lib = import 'common-functions.ds';` | `<bean ref="commonFunctions" method="..." />` |
| 是否需要文件 | 需要 `common-functions.ds` 文件 | 无需额外文件，Java 类自动注册 |
| 适用范围 | 数据映射/转换逻辑 | 路由流程控制、属性设置等 |
| 修改生效 | 修改 DS 文件后重新加载路由 | 需要重新编译部署 |

### 选择建议

- **DS 转换脚本内的函数复用** → 使用 `import 'common-functions.ds'`
- **路由 XML 中需要调用公共逻辑** → 使用 `<bean ref="commonFunctions" />`
- **Java Processor 中需要调用** → 使用 `CommonFunctions.getInstance().xxx()`
- 两种方式可以**同时使用**，互不冲突

---


### 选择建议（三种方式）

- **DS 脚本内快速复用** → `import 'common-functions.ds'`（灵活，热更新）
- **路由 XML / Java Processor** → `<bean ref="commonFunctions" />`

---

**文档创建时间**: 2025-10-16  
**最后更新**: 2026-02-09 
**适用版本**: DataSonnet 2.0+ / datasonnet-mapper 3.0+  
**项目**: LightESB Platform

