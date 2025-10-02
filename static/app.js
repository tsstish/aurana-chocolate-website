document.addEventListener('DOMContentLoaded', () => {
    // 1. Инициализация состояния корзины
    const cart = {};
    const productElements = document.querySelectorAll('.product-card');
    const cartItemsElement = document.getElementById('cart-items');
    const cartTotalDisplay = document.getElementById('cart-total-display');
    const orderDetailsJsonInput = document.getElementById('order_details_json');
    const submitButton = document.getElementById('submit-order');
    const formHint = document.getElementById('form-hint');

    /**
     * 2. Обновляет отображение корзины и поля JSON
     */
    function updateCartDisplay() {
        let total = 0;
        let hasItems = false;
        cartItemsElement.innerHTML = '';

        const cartDetails = []; // Массив для JSON-данных

        for (const id in cart) {
            const item = cart[id];
            if (item.qty > 0) {
                hasItems = true;
                const itemTotal = item.qty * item.price;
                total += itemTotal;

                // Создание элемента в списке корзины
                const itemDiv = document.createElement('div');
                itemDiv.className = 'cart-item';
                itemDiv.innerHTML = `
                    <p>${item.name}</p>
                    <p>${item.qty} шт. x ${item.price} ₽ = ${itemTotal} ₽</p>
                `;
                cartItemsElement.appendChild(itemDiv);

                // Заполнение массива для JSON
                cartDetails.push({
                    id: item.id,
                    name: item.name,
                    qty: item.qty,
                    price: item.price,
                    total: itemTotal
                });
            }
        }

        // Если корзина пуста
        if (!hasItems) {
            cartItemsElement.innerHTML = '<p>Корзина пуста. Добавьте товар, чтобы оформить заказ.</p>';
            orderDetailsJsonInput.value = '';
            submitButton.disabled = true;
            formHint.style.display = 'block';
        } else {
            // Если в корзине есть товары
            cartTotalDisplay.textContent = total.toLocaleString();
            orderDetailsJsonInput.value = JSON.stringify(cartDetails, null, 2);
            submitButton.disabled = false;
            formHint.style.display = 'none';
        }
    }

    /**
     * 3. Инициализация корзины из данных на странице
     */
    productElements.forEach(card => {
        const id = card.dataset.id;
        const price = parseInt(card.dataset.price);
        const name = card.dataset.name;
        
        cart[id] = {
            id: id,
            name: name,
            price: price,
            qty: 0
        };
    });

    /**
     * 4. Обработчик нажатия на кнопки +/-
     */
    document.body.addEventListener('click', (e) => {
        if (e.target.classList.contains('qty-plus') || e.target.classList.contains('qty-minus')) {
            const id = e.target.dataset.id;
            const isPlus = e.target.classList.contains('qty-plus');

            if (cart[id]) {
                if (isPlus) {
                    cart[id].qty += 1;
                } else if (cart[id].qty > 0) {
                    cart[id].qty -= 1;
                }
                
                // Обновляем число на карточке
                document.getElementById(`qty-${id}`).textContent = cart[id].qty;

                // Обновляем корзину
                updateCartDisplay();
            }
        }
    });

    // Инициализация корзины при загрузке
    updateCartDisplay();
});