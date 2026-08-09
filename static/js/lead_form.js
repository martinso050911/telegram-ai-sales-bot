document.addEventListener('DOMContentLoaded', () => {
    const leadForm = document.getElementById('lead-form');
    const formAlert = document.getElementById('form-alert');

    if (!leadForm) return;

    leadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = {
            name: document.getElementById('name').value.trim(),
            phone: document.getElementById('phone').value.trim(),
            email: document.getElementById('email').value.trim(),
            company: document.getElementById('company').value.trim(),
            message: document.getElementById('message').value.trim(),
        };

        formAlert.className = 'alert hidden';
        const submitBtn = leadForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerText = 'Отправка... ⏳';

        try {
            const response = await fetch('/api/leads', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                formAlert.className = 'alert alert-success';
                formAlert.innerText = '🎉 Спасибо! Ваша заявка успешно отправлена. Менеджер свяжется с вами в течение 10 минут.';
                leadForm.reset();
            } else {
                formAlert.className = 'alert alert-error';
                formAlert.innerText = '⚠️ ' + (data.detail || 'Не удалось отправить заявку. Попробуйте еще раз.');
            }
        } catch (err) {
            console.error('Lead submit error:', err);
            formAlert.className = 'alert alert-error';
            formAlert.innerText = '⚠️ Ошибка подключения к серверу.';
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = 'Отправить заявку 🚀';
        }
    });
});
