# Support

Thank you for using **Zen AI Pentest**! This document provides information on how to get help, report issues, and engage with our community.

---

## 📚 Documentation

Before reaching out for support, please check our comprehensive documentation:

- **[Getting Started Guide](docs/tutorials/getting-started.md)** - First steps with Zen AI Pentest
- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[API Documentation](docs/API.md)** - REST API reference
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and components
- **[Troubleshooting](docs/setup/VIRTUALBOX_SETUP.md)** - Common issues and solutions

---

## 🐛 Reporting Issues

Found a bug? Please help us improve by reporting it:

1. **Check existing issues**: Search [GitHub Issues](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues) to avoid duplicates
2. **Use the template**: File a [Bug Report](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues/new?template=bug_report.md)
3. **Provide details**: Include steps to reproduce, expected vs actual behavior, and environment info

---

## 💡 Feature Requests

Have an idea for a new feature? We'd love to hear it:

1. **Check existing requests**: Search [GitHub Issues](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues)
2. **Use the template**: Submit a [Feature Request](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues/new?template=feature_request.md)
3. **Describe the use case**: Explain the problem and how your feature would solve it

---

## 💬 Community Support

### GitHub Discussions
Join our [GitHub Discussions](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions) for:
- Q&A and troubleshooting
- Sharing ideas and best practices
- Connecting with other users
- Showcasing your projects

### Discord Community
Get real-time help from our community:
- **Discord**: [https://discord.gg/BSmCqjhY](https://discord.gg/BSmCqjhY)
- Active community of security professionals
- Direct access to core team members
- Channels for different topics (general, development, security)

---

## 🔒 Security Issues

**IMPORTANT**: For security vulnerabilities, please do NOT open public issues.

Instead:
1. Report privately via [GitHub Security Advisories](https://github.com/SHAdd0WTAka/zen-ai-pentest/security/advisories/new)
2. Email: security@zen-ai-pentest.dev
3. We'll respond within 48 hours with next steps

See [SECURITY.md](SECURITY.md) for our security policy.

---

## 📧 Commercial Support

For enterprise users requiring dedicated support:

| Plan | Response Time | Features |
|------|--------------|----------|
| **Community** | Best effort | GitHub Issues, Discord |
| **Enterprise** | 24 hours | Email support, SLA |
| **Premium** | 4 hours | Phone support, dedicated engineer |

Contact: support@zen-ai-pentest.dev

---

## 🆘 Emergency Support

For critical production issues:

1. Check [Status Page](https://status.zen-ai-pentest.dev)
2. Email: emergency@zen-ai-pentest.dev (subject: URGENT)
3. Include: Organization name, issue description, impact level

---

## 🎯 Common Questions

### Installation Issues
```bash
# Verify Python version (3.9+ required)
python --version

# Check dependencies
pip install -r requirements.txt --dry-run

# Run health check
python -c "from zen_ai_pentest import health_check; health_check()"
```

### API Connection Problems
- Verify the server is running: `curl http://localhost:8000/health`
- Check your `.env` configuration
- Ensure port 8000 is not blocked by firewall

### Docker Deployment
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Reset environment
docker-compose down -v && docker-compose up -d
```

---

## 🤝 Contributing to Support

Help others by:
- Answering questions in Discussions
- Improving documentation
- Sharing your configurations and setups
- Writing blog posts or tutorials

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📋 Support Request Checklist

When requesting help, please include:

- [ ] Zen AI Pentest version (`zen-ai-pentest --version`)
- [ ] Python version (`python --version`)
- [ ] Operating system and version
- [ ] Installation method (pip, docker, source)
- [ ] Complete error message or stack trace
- [ ] Steps to reproduce the issue
- [ ] What you've already tried

---

## 🌐 Resources

- **Website**: https://zen-ai-pentest.dev
- **Documentation**: https://docs.zen-ai-pentest.dev
- **Blog**: https://blog.zen-ai-pentest.dev
- **YouTube**: https://youtube.com/@zen-ai-pentest

---

<p align="center">
  <b>We're here to help! Don't hesitate to reach out.</b><br>
  <sub>© 2026 Zen AI Pentest. All rights reserved.</sub>
</p>
