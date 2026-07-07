import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'

const STORAGE_KEY = 'platform_form_config'

interface FormData {
  base_url: string
  login_url: string
  test_username: string
  test_password: string
  token_field: string
  token_type: string
  auth_header: string
  marker: string
  order_prefix: string
  loop_count: number
  workflow_type: string
}

type WorkflowType = 'order_only' | 'pay_receive' | 'receive_pay'

type WorkflowCard = {
  id: string          // 全局唯一标识（切卡逻辑依赖此字段）
  key: WorkflowType   // 传给后端的 workflow_type
  label: string
  tag: string
  markers: string[]   // 该卡片允许的 marker 范围
}

const WORKFLOW_CARDS: WorkflowCard[] = [
  {
    id: 'order_only',
    key: 'order_only',
    label: '仅订单',
    tag: '默认',
    markers: Array.from({ length: 12 }, (_, idx) => `order${idx + 1}`),
  },
  {
    id: 'pay_receive',
    key: 'pay_receive',
    label: '订单+应付',
    tag: '默认',
    markers: Array.from({ length: 7 }, (_, idx) => `order_pay_receive${idx + 1}`),
  },
  {
    id: 'pay_receive_full',
    key: 'pay_receive',
    label: '订单+应付+应收',
    tag: '默认',
    markers: Array.from({ length: 6 }, (_, idx) => `order_pay_receive${idx + 8}`),
  },
  {
    id: 'receive_pay',
    key: 'receive_pay',
    label: '订单+应收',
    tag: '扩展',
    markers: Array.from({ length: 6 }, (_, idx) => `order_receive_pay${idx + 1}`),
  },
  {
    id: 'receive_pay_full',
    key: 'receive_pay',
    label: '订单+应收+应付',
    tag: '扩展',
    markers: Array.from({ length: 7 }, (_, idx) => `order_receive_pay${idx + 7}`),
  },
]

const DEFAULT_CARD_ID = 'order_only'
const DEFAULT_CARD = WORKFLOW_CARDS[0]
const DEFAULT_MARKER = DEFAULT_CARD.markers[0]

const DEFAULTS: FormData = {
  base_url: 'https://fin-tidb.21eflag.com/',
  login_url: '/api/home/login/userLogin',
  test_username: '',
  test_password: '',
  token_field: 'data.token',
  token_type: '',
  auth_header: 'Authorization',
  marker: DEFAULT_MARKER,
  order_prefix: 'lele',
  loop_count: 1,
  workflow_type: DEFAULT_CARD_ID,
}

function readSaved(): Partial<FormData> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const data = JSON.parse(raw) as FormData
    const card = WORKFLOW_CARDS.find(item => item.id === data.workflow_type)
    if (!card) {
      return { ...data, workflow_type: DEFAULT_CARD_ID, marker: DEFAULT_MARKER }
    }
    const markerValid = card.markers.includes(data.marker)
    return {
      ...data,
      workflow_type: card.id,
      marker: markerValid ? data.marker : card.markers[0],
    }
  } catch {
    return {}
  }
}

export const useFormStore = defineStore('form', () => {
  const initial = { ...DEFAULTS, ...readSaved() } as FormData
  const data = reactive<FormData>(initial)

  // 响应式计算属性，切换卡片后模板会自动更新
  const activeCard = computed(() =>
    WORKFLOW_CARDS.find(card => card.id === data.workflow_type) ?? DEFAULT_CARD
  )
  const workflowCards = computed(() => WORKFLOW_CARDS)

  function setWorkflowCard(id: string) {
    const card = WORKFLOW_CARDS.find(item => item.id === id)
    if (!card) return
    data.workflow_type = card.id
    data.marker = card.markers[0]
    save()
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }

  function reset() {
    Object.assign(data, { ...DEFAULTS })
    localStorage.removeItem(STORAGE_KEY)
  }

  // 当直接修改 data.marker 时，自动同步到对应卡片
  function syncFromCard() {
    const card = WORKFLOW_CARDS.find(c => c.markers.includes(data.marker))
    if (card) {
      data.workflow_type = card.id
    }
  }

  return {
    data,
    patch(values: Partial<FormData>) {
      Object.assign(data, values)
      syncFromCard()
      save()
    },
    save,
    reset,
    setWorkflowCard,
    workflowCards,
    activeCard,
  }
})
