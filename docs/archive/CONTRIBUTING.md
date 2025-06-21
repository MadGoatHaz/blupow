# Contributing to BluPow

Thank you for your interest in contributing to BluPow! We welcome contributions from the community and are excited to work with you to make BluPow the best Renogy inverter integration for Home Assistant.

## 🌟 **Ways to Contribute**

### **🐛 Bug Reports**
- Report issues with detailed information
- Include logs, configuration, and device information
- Use the provided issue templates

### **💡 Feature Requests**
- Suggest new features or improvements
- Provide use cases and implementation ideas
- Participate in feature discussions

### **📝 Documentation**
- Improve existing documentation
- Add examples and tutorials
- Translate documentation to other languages

### **🔧 Code Contributions**
- Fix bugs and implement features
- Improve performance and reliability
- Add support for new devices

### **🧪 Testing**
- Test with different devices and configurations
- Validate stability and performance
- Report compatibility results

### **💝 Financial Support**
- [GitHub Sponsors](https://github.com/sponsors/MadGoatHaz)
- [PayPal Donations](https://paypal.me/MadGoatHaz)

## 🚀 **Getting Started**

### **Development Environment Setup**

1. **Fork the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/blupow.git
   cd blupow
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements-dev.txt
   ```

3. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

### **Testing Setup**

1. **Run Unit Tests**
   ```bash
   python -m pytest tests/unit/
   ```

2. **Run Integration Tests**
   ```bash
   python -m pytest tests/integration/
   ```

3. **Run Stability Tests**
   ```bash
   python scripts/stability_test.py
   ```

## 📋 **Development Guidelines**

### **Code Style**
- Follow PEP 8 Python style guidelines
- Use type hints for all functions
- Write descriptive docstrings
- Keep functions focused and small

### **Testing Requirements**
- Write tests for all new features
- Maintain test coverage above 80%
- Include integration tests for hardware interactions
- Test with real devices when possible

### **Documentation Standards**
- Update documentation for all changes
- Include code examples in docstrings
- Write clear commit messages
- Update CHANGELOG.md for user-facing changes

## 🔄 **Pull Request Process**

### **Before Submitting**
1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation

3. **Test Thoroughly**
   ```bash
   # Run all tests
   python -m pytest
   
   # Run linting
   flake8 custom_components/blupow/
   
   # Run type checking
   mypy custom_components/blupow/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add support for new device model"
   ```

### **Commit Message Format**
Use conventional commits format:
```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

### **Pull Request Checklist**
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if user-facing)
- [ ] Commit messages follow conventional format

## 🧪 **Testing Guidelines**

### **Device Testing**
When testing with real devices:
- Document device model and firmware version
- Test all sensor readings for accuracy
- Verify connection stability over extended periods
- Test error recovery scenarios

### **Test Categories**
1. **Unit Tests** - Test individual functions
2. **Integration Tests** - Test component interactions
3. **Device Tests** - Test with real hardware
4. **Stability Tests** - Long-running reliability tests

### **Test Data**
- Use realistic test data based on actual device readings
- Include edge cases and error conditions
- Test with different device configurations

## 📖 **Documentation Contributions**

### **Types of Documentation**
- **User Guides** - Installation and configuration
- **Developer Docs** - Technical architecture and APIs
- **Troubleshooting** - Common issues and solutions
- **Examples** - Configuration examples and use cases

### **Documentation Standards**
- Write in clear, accessible language
- Include code examples and screenshots
- Provide step-by-step instructions
- Keep documentation up-to-date with code changes

## 🤝 **Community Guidelines**

### **Code of Conduct**
- Be respectful and inclusive
- Help others learn and grow
- Provide constructive feedback
- Celebrate contributions of all sizes

### **Communication**
- Use GitHub Issues for bug reports and feature requests
- Use GitHub Discussions for questions and ideas
- Be patient and helpful with new contributors
- Ask questions when you need clarification

## 🎯 **Priority Areas**

### **High Priority**
- Device compatibility expansion
- Stability and reliability improvements
- Performance optimizations
- Documentation improvements

### **Medium Priority**
- New sensor types and metrics
- Advanced configuration options
- Dashboard templates and examples
- Internationalization

### **Future Vision**
- Multi-protocol support (Modbus TCP, CAN, etc.)
- Cloud integration options
- Mobile app companion
- AI-powered optimization features

## 💰 **Monetization Philosophy**

BluPow follows a **value-based support model**:
- All features remain free and open source
- Users contribute what they feel the project is worth
- Financial support helps maintain and expand the project
- Contributors are recognized and appreciated

### **How Contributions Help**
- **Development Time** - Allows dedicated development work
- **Hardware Testing** - Purchase devices for compatibility testing
- **Infrastructure** - Hosting, CI/CD, and development tools
- **Community Growth** - Marketing and community building

## 🏆 **Recognition**

### **Contributor Recognition**
- Contributors listed in README.md
- Special recognition for significant contributions
- Beta access to new features
- Direct communication with maintainers

### **Types of Recognition**
- **Code Contributors** - Direct code contributions
- **Documentation Contributors** - Improve project documentation
- **Testing Contributors** - Device testing and validation
- **Community Contributors** - Help users and build community
- **Financial Contributors** - Support project development

## 📞 **Getting Help**

### **Development Questions**
- Create a GitHub Discussion
- Join our community chat
- Email: dev@blupow.dev

### **Bug Reports**
- Use GitHub Issues
- Provide detailed information
- Include logs and configuration

### **Feature Requests**
- Use GitHub Discussions
- Describe use case and benefits
- Participate in design discussions

## 🎉 **Thank You**

Every contribution, no matter how small, helps make BluPow better for everyone. Whether you're fixing a typo, adding a feature, or supporting the project financially, you're helping build the future of home energy monitoring.

Together, we're creating something amazing! 🌟

---

*For questions about contributing, reach out to the maintainers or create a GitHub Discussion.* 