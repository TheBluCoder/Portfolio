// A skill's `icon` field is the single source of truth for how to render it:
// - an Iconify id, e.g. "devicon:vuejs" or "simple-icons:googlegemini" — rendered via <Icon>
// - a Font Awesome class string, e.g. "fa-brands fa-js" — rendered via <i>
// The prefix (text before the colon) tells us which one it is; no name-based guessing needed.
export function resolveSkillIcon(skill) {
  const name = typeof skill === 'string' ? skill : skill?.name
  const icon = typeof skill === 'object' && skill ? skill.icon : null
  const isIconifyId = typeof icon === 'string' && icon.includes(':')

  return {
    icon: isIconifyId ? icon : null,
    label: name || 'Skill',
    fallbackIcon: isIconifyId ? null : icon || null,
  }
}
