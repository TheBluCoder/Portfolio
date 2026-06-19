/**
 * Parses a GitHub README.md into structured data for the portfolio homepage.
 *
 * Expected README structure:
 *   ## About        — free-form prose
 *   ## Experience   — ### entries with **Company** | Role / *dates* / - tasks
 *   ## Education    — ### entries with **Institution** / *dates* | GPA / program line
 *   ## Skills       — ### Category / comma list or - bullets
 *
 * See BLUCODER_README_TEMPLATE.md for the full format contract.
 */

/** Split markdown into a map of { lowercaseHeading: bodyText } by ## headings */
function splitIntoSections(markdown) {
  const sections = {}
  const lines = markdown.split('\n')
  let current = null
  let acc = []

  for (const line of lines) {
    const h2 = line.match(/^## (.+)$/)
    if (h2) {
      if (current !== null) sections[current] = acc.join('\n').trim()
      current = h2[1].trim().toLowerCase()
      acc = []
    } else if (current !== null) {
      acc.push(line)
    }
  }
  if (current !== null) sections[current] = acc.join('\n').trim()

  return sections
}

/** Split a section body into ### sub-blocks */
function splitSubBlocks(text) {
  return text.split(/(?=^### )/m).filter((b) => b.trim().startsWith('###'))
}

export function parseExperience(text) {
  return splitSubBlocks(text)
    .map((block) => {
      const lines = block.split('\n')
      const jobTitle = lines[0].replace(/^###\s*/, '').trim()
      let company = '', position = '', dateStart = '', dateEnd = ''
      const tasks = []

      for (const line of lines.slice(1)) {
        const t = line.trim()
        if (!t) continue

        // **Company** | Position  or  **Company** · Position
        const companyMatch = t.match(/^\*\*(.+?)\*\*\s*[|·]\s*(.+)$/)
        if (companyMatch) {
          company = companyMatch[1].trim()
          position = companyMatch[2].trim()
          continue
        }

        // *Start – End*  (em dash, en dash, or hyphen)
        const dateMatch = t.match(/^\*(.+?)\s*[–—-]\s*(.+?)\*/)
        if (dateMatch) {
          dateStart = dateMatch[1].trim()
          dateEnd = dateMatch[2].trim()
          continue
        }

        // - task
        if (t.startsWith('- ')) tasks.push(t.slice(2).trim())
      }

      return jobTitle ? { jobTitle, company, position, dateStart, dateEnd, tasks } : null
    })
    .filter(Boolean)
}

export function parseEducation(text) {
  return splitSubBlocks(text)
    .map((block) => {
      const lines = block.split('\n')
      const degree = lines[0].replace(/^###\s*/, '').trim()
      let institution = '', program = '', dateStart = '', dateEnd = '', gpa = ''

      for (const line of lines.slice(1)) {
        const t = line.trim()
        if (!t) continue

        // **Institution**
        const instMatch = t.match(/^\*\*(.+?)\*\*$/)
        if (instMatch) { institution = instMatch[1].trim(); continue }

        // *Start – End* | GPA: X.X
        const dateMatch = t.match(/^\*(.+?)\s*[–—-]\s*(.+?)\*(?:\s*\|\s*GPA:\s*(.+))?$/)
        if (dateMatch) {
          dateStart = dateMatch[1].trim()
          dateEnd = dateMatch[2].trim()
          gpa = dateMatch[3]?.trim() || ''
          continue
        }

        // Plain line = program description
        if (!t.startsWith('*') && !t.startsWith('#') && !t.startsWith('-') && !program) {
          program = t
        }
      }

      return degree ? { degree, institution, program, dateStart, dateEnd, gpa } : null
    })
    .filter(Boolean)
}

export function parseSkills(text) {
  return splitSubBlocks(text)
    .map((block) => {
      const lines = block.split('\n')
      const category = lines[0].replace(/^###\s*/, '').trim()
      const technologies = []

      for (const line of lines.slice(1)) {
        const t = line.trim()
        if (!t) continue
        if (t.startsWith('- ')) {
          technologies.push(t.slice(2).trim())
        } else {
          technologies.push(...t.split(',').map((s) => s.trim()).filter(Boolean))
        }
      }

      return category && technologies.length ? { category, technologies } : null
    })
    .filter(Boolean)
}

/** Main entry point — returns structured data from a raw README string */
export function parseReadme(markdown) {
  if (!markdown) return { about: null, experience: [], education: [], skills: [] }

  const sections = splitIntoSections(markdown)

  return {
    about:      sections['about'] ?? null,
    experience: sections['experience'] ? parseExperience(sections['experience']) : [],
    education:  sections['education']  ? parseEducation(sections['education'])   : [],
    skills:     sections['skills']     ? parseSkills(sections['skills'])         : [],
  }
}
