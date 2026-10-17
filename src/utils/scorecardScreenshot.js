export async function downloadScorecardScreenshot(element, filename) {
  const { domToBlob } = await import('modern-screenshot')
  await document.fonts.ready
  const blob = await domToBlob(element, {
    type: 'image/png',
    scale: 2,
    backgroundColor: getComputedStyle(document.body).backgroundColor,
    features: { restoreScrollPosition: true },
    filter: node => node.nodeType !== 1 || (
      !node.hasAttribute('data-screenshot-exclude') && getComputedStyle(node).display !== 'none'
    ),
    onCloneEachNode: node => {
      if (node.tagName === 'INPUT' && node.type === 'checkbox') node.toggleAttribute('checked', node.checked)
    }
  })
  if (!blob) throw new Error('無法產生 PNG 圖片')
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.append(link)
  try {
    link.click()
  } finally {
    link.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
}
