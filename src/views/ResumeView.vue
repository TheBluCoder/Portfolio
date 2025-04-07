<script setup>
import { DownloadIcon } from 'lucide-vue-next'
</script>

<template>
  <section class="min-h-screen w-full bg-black p-8 text-white">
    <!-- Tech Stack Section -->
    <div class="max-w-7xl mx-auto mb-16 fade-in-section">
      <h1 class="text-4xl font-bold mb-10">here's my tech stack!</h1>
      <hr class="border-gray-700 mb-10" />

      <div class="grid grid-cols-1 md:grid-cols-3 gap-16">
        <!-- Front-end -->
        <div>
          <h2 class="text-2xl font-bold text-green-500 mb-6">front-end</h2>
          <p class="text-gray-300 mb-6">
            Definitely not my forte, but when I do try, I try. Here is what I love to use:
          </p>
          <ul class="space-y-3">
            <li class="flex items-center">
              <span class="text-green-500 mr-2">►</span>
              <span>VueJs</span>
              <i class="fa-brands fa-vuejs ml-3"></i>
            </li>
            <li class="flex items-center">
              <span class="text-green-500 mr-2">►</span>
              <span>ShadCn-vue</span>
            </li>
            <li class="flex items-center">
              <span class="text-green-500 mr-2">►</span>
              <span>Tailwind CSS</span>
            </li>
          </ul>
        </div>

        <!-- Languages -->
        <div>
          <h2 class="text-2xl font-bold text-green-500 mb-6">languages</h2>
          <p class="text-gray-300 mb-6">I am familiar with these programming languages:</p>
          <div class="grid grid-cols-2 gap-3">
            <ul class="space-y-3">
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>Python</span>
              </li>
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>C</span>
              </li>
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>Solidity</span>
              </li>
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>SQL</span>
              </li>
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>Bash</span>
              </li>
            </ul>
            <ul class="space-y-3">
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>Java</span>
              </li>
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>Php/Laravel</span>
              </li>
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>JavaScript</span>
              </li>
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>HTML/CSS</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Machine Learning -->
        <div>
          <h2 class="text-2xl font-bold text-green-500 mb-6">Artificial Intelligence</h2>
          <p class="text-gray-300 mb-6">
            I have experiencing setting up my own Agent and MCP server
          </p>
          <div class="grid grid-cols-2 gap-3">
            <ul class="space-y-3">
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>FastMcp</span>
              </li>
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>LangChain</span>
              </li>
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>Pytorch</span>
              </li>
            </ul>
            <ul class="space-y-3">
              <li class="flex items-center">
                <span class="text-green-500 mr-2">►</span>
                <span>PyTorch</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Experience Section -->
    <div class="max-w-7xl mx-auto fade-in-section">
      <div class="flex justify-between items-center mb-10 gap-2">
        <h1 class="text-4xl font-bold mr-1">Experience</h1>
        <a
          href="#"
          class="bg-blue-900 hover:bg-blue-800 text-white py-2 px-4 rounded-md flex items-center transition-colors"
        >
          <DownloadIcon class="mr-2 h-5 w-5" />
          <span>Download Resume</span>
        </a>
      </div>

      <!-- Experience Timeline -->
      <div class="relative">
        <!-- Timeline line -->
        <div class="absolute left-3 top-0 bottom-0 w-0.5 bg-gray-700"></div>

        <!-- Experience items -->
        <div class="mb-14 pl-12 relative">
          <div class="absolute left-0 top-2 bg-blue-600 rounded-full w-6 h-6"></div>
          <div class="timeline-content">
            <h2 class="text-2xl font-bold flex items-baseline whitespace-nowrap">
              IT support Coordinator
              <span class="text-gray-500/80 text-sm font-light ml-2">Intern</span>
            </h2>
            <p class="text-gray-400 mt-1">Taggart Group Of Companies. • 2024 - Present</p>
            <ul class="mt-4 text-gray-300 space-y-3 list-disc pl-5">
              <li>
                Resolved Over 350 service desk tickets that involved system administration, hardware
                troubleshooting and network troubleshooting. Making me the person with the thirdmost
                resolved tickets in the company currently
              </li>
              <li>
                Built a chatbot prototype that uses mcp and is integrated with topdesk (the
                ticketing system) to assist the IT team with troubleshooting as well as make
                onboarding easier for new onboarded members
              </li>
            </ul>
          </div>
        </div>

        <div class="mb-14 pl-12 relative">
          <div class="absolute left-0 top-2 bg-blue-600 rounded-full w-6 h-6"></div>
          <div class="timeline-content">
            <h2 class="text-2xl font-bold flex items-baseline whitespace-nowrap">
              FullStack Developer
              <span class="text-gray-500/80 text-sm font-light ml-2">Volunteer</span>
            </h2>
            <p class="text-gray-400 mt-1">Family Hub Foundation • 2025 - present</p>
            <ul class="mt-4 text-gray-300 space-y-3 list-disc pl-5">
              <li>
                Recently Joined Family Hub Foundation team as a volunteer for a fullStack Developer
                role.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Education Section -->
    <div class="max-w-7xl mx-auto fade-in-section mt-20">
      <h1 class="text-4xl font-bold mb-10">Education</h1>

      <!-- Education Timeline -->
      <div class="relative">
        <!-- Timeline line -->
        <div class="absolute left-3 top-0 bottom-0 w-0.5 bg-gray-700"></div>

        <!-- Education items -->
        <div class="mb-14 pl-12 relative">
          <div class="absolute left-0 top-2 bg-blue-600 rounded-full w-6 h-6"></div>
          <div class="timeline-content">
            <h2 class="text-2xl font-bold">Advance Diploma</h2>
            <p class="text-gray-400 mt-1">Algonquin College • 2023 - 2026</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.fade-in-section {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeIn 0.8s ease forwards;
}

@keyframes fadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-section:nth-child(2) {
  animation-delay: 0.3s;
}

.timeline-content {
  position: relative;
  border-left: none;
  padding-left: 0;
}

.timeline-content::before {
  content: '';
  position: absolute;
  top: 13px;
  left: -20px;
  width: 14px;
  height: 2px;
  background-color: #6b7280;
}
</style>
