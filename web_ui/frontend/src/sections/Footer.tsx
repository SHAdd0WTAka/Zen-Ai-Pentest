import {
  Shield,
  Github,
  Twitter,
  MessageCircle,
  Heart,
  ExternalLink,
  Mail,
} from 'lucide-react';

const footerLinks = {
  product: [
    { name: 'Features', href: '#features' },
    { name: 'Tools', href: '#tools' },
    { name: 'Architecture', href: '#architecture' },
    { name: 'API', href: '#api' },
  ],
  resources: [
    { name: 'Documentation', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/README.md' },
    { name: 'Quickstart', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/QUICKSTART.md' },
    { name: 'API Reference', href: '#api' },
    { name: 'Examples', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/tree/main/examples' },
  ],
  community: [
    { name: 'GitHub', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest' },
    { name: 'Discord', href: 'https://discord.gg/BSmCqjhY' },
    { name: 'Issues', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues' },
    { name: 'Discussions', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/discussions' },
  ],
  legal: [
    { name: 'License', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/LICENSE' },
    { name: 'Security', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/SECURITY.md' },
    { name: 'Contributing', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/CONTRIBUTING.md' },
    { name: 'Code of Conduct', href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/CODE_OF_CONDUCT.md' },
  ],
};

const socialLinks = [
  { name: 'GitHub', icon: Github, href: 'https://github.com/SHAdd0WTAka/Zen-Ai-Pentest' },
  { name: 'Discord', icon: MessageCircle, href: 'https://discord.gg/BSmCqjhY' },
  { name: 'Twitter', icon: Twitter, href: '#' },
  { name: 'Email', icon: Mail, href: 'mailto:contact@zen-ai-pentest.io' },
];

export function Footer() {
  const scrollToSection = (href: string) => {
    if (href.startsWith('#')) {
      const element = document.querySelector(href);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <footer className="relative py-16 overflow-hidden border-t border-slate-800/50">
      {/* Background */}
      <div className="absolute inset-0 bg-slate-950" />
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-cyan-500/5 rounded-full blur-[128px]" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main Footer Content */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-8 mb-12">
          {/* Brand */}
          <div className="col-span-2">
            <a
              href="#"
              className="flex items-center gap-2 mb-4"
              onClick={(e) => {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              <Shield className="w-8 h-8 text-cyan-400" />
              <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                Zen-AI-Pentest
              </span>
            </a>
            <p className="text-slate-400 text-sm mb-6 max-w-xs">
              AI-powered penetration testing framework with 40+ security tools,
              autonomous agents, and enterprise-grade safety controls.
            </p>

            {/* Social Links */}
            <div className="flex gap-3">
              {socialLinks.map((social) => (
                <a
                  key={social.name}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg bg-slate-900/50 border border-slate-800/50 text-slate-400 hover:text-white hover:border-slate-700/50 transition-all"
                  aria-label={social.name}
                >
                  <social.icon className="w-5 h-5" />
                </a>
              ))}
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="font-semibold text-white mb-4">Product</h4>
            <ul className="space-y-2">
              {footerLinks.product.map((link) => (
                <li key={link.name}>
                  <button
                    onClick={() => scrollToSection(link.href)}
                    className="text-sm text-slate-400 hover:text-white transition-colors"
                  >
                    {link.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h4 className="font-semibold text-white mb-4">Resources</h4>
            <ul className="space-y-2">
              {footerLinks.resources.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-slate-400 hover:text-white transition-colors inline-flex items-center gap-1"
                  >
                    {link.name}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Community Links */}
          <div>
            <h4 className="font-semibold text-white mb-4">Community</h4>
            <ul className="space-y-2">
              {footerLinks.community.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-slate-400 hover:text-white transition-colors inline-flex items-center gap-1"
                  >
                    {link.name}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="font-semibold text-white mb-4">Legal</h4>
            <ul className="space-y-2">
              {footerLinks.legal.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-slate-400 hover:text-white transition-colors inline-flex items-center gap-1"
                  >
                    {link.name}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="py-6 border-y border-slate-800/50 mb-6">
          <div className="flex flex-wrap justify-center gap-8">
            {[
              { value: '205+', label: 'Stars' },
              { value: '29', label: 'Forks' },
              { value: '780+', label: 'Commits' },
              { value: '6', label: 'Contributors' },
              { value: 'v2.3.9', label: 'Version' },
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-lg font-bold text-white">{stat.value}</div>
                <div className="text-xs text-slate-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-slate-500">
            © 2026 Zen-AI-Pentest. Open source under MIT License.
          </p>
          <p className="text-sm text-slate-500 flex items-center gap-1">
            Made with <Heart className="w-4 h-4 text-red-500 fill-red-500" /> by{' '}
            <a
              href="https://github.com/SHAdd0WTAka"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              SHAdd0WTAka
            </a>{' '}
            and contributors
          </p>
        </div>
      </div>
    </footer>
  );
}
