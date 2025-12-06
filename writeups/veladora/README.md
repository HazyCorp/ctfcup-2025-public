# Veladora
## Базовый сценарий
Пользователь заходит в бар и заказывает напитки, оплачивает счёт и разговаривает с барменом. Пользователь может посмотреть свои чеки в личном кабинете и восстановить диалог с барменом с помощью 32-байтного значения встречающегося в диалоге.

### Все фичи
- Заказ напитков и добавление в счёт
- Оплата счёта
- Диалог с барменом
- Восстановление диалога с барменом
- Просмотр оплаченного счёта

## Архитектура
Простое веб-приложение на Go с использованием фреймворка Gin.

## Уязвимости

### Возможность внедрения произвольных данных в диалог произвольного пользователя

При отправке бармену любого сообщения мы можем указать имя пользователя, при этом нет никакой проверки, что это имя нашего текущего пользователя, то есть мы можем добавить данные в диалог любого пользователя.

```golang
if req.Username != "" {
	var resolvedUserID int
	lookupErr := database.DB.QueryRow(ctx,
		"SELECT id FROM users WHERE username = $1", req.Username).Scan(&resolvedUserID)
	if lookupErr == nil {
		conversationOwnerID = resolvedUserID
	}
}
```

Это позволит нам восстановить диалог для пользователя через другой функционал у бармена.

```golang
if req.Username != "" {
	err = database.DB.QueryRow(ctx,
		"SELECT id FROM users WHERE username = $1", req.Username).Scan(&userID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}
} else {
	userIDVal, _ := c.Get("user_id")
	userID = userIDVal.(int)
}
```

### IDOR и предсказуемый ID для оплаченных счетов

При оплате счёта генерируется чек. При этом его ID предсказуемый.

```sql
CREATE OR REPLACE FUNCTION generate_payment_id(p_u VARCHAR, p_b INTEGER) RETURNS VARCHAR AS $$
	DECLARE
		vu VARCHAR;
		vp VARCHAR;
		vt INTEGER;
		vux VARCHAR;
		vbx INTEGER;
		vbl INTEGER;
		i INTEGER;
		hb VARCHAR(2);
		bv INTEGER;
		xl INTEGER;
	BEGIN
		vu := encode(convert_to(LOWER(p_u), 'UTF8'), 'hex');
		vt := FLOOR(RANDOM() * 16)::INTEGER;
		vbl := LENGTH(vu) * 4;
		vux := '';
		FOR i IN 1..LENGTH(vu) BY 2 LOOP
			hb := SUBSTRING(vu FROM i FOR 2);
			bv := ('x' || hb)::bit(8)::integer;
			xl := bv # vt;
			vux := vux || LPAD(TO_HEX(xl), 2, '0');
		END LOOP;
		vbx := p_b # vt;
		vp := vux || '_' || LPAD(TO_HEX(vbx), 4, '0') || '_' || LPAD(TO_HEX(vt), 2, '0');
		RETURN vp;
	END;
```

Также в коде доступа к чеку нет проверки, что пользователь является владельцем чека.

```golang
paymentID := c.Param("payment_id")
if paymentID == "" {
	c.JSON(http.StatusBadRequest, gin.H{"error": "Payment ID required"})
	return
}

ctx := c.Request.Context()

var bill models.Bill
err := database.DB.QueryRow(ctx,
	"SELECT id, user_id, amount, COALESCE(comment, ''), COALESCE(status, 'active'), COALESCE(payment_id, ''), created_at FROM bills WHERE payment_id = $1",
	paymentID).Scan(&bill.ID, &bill.UserID, &bill.Amount, &bill.Comment, &bill.Status, &bill.PaymentID, &bill.CreatedAt)
if err != nil {
	c.JSON(http.StatusNotFound, gin.H{"error": "Bill not found"})
	return
}
```


## Эксплуатация

### Возможность внедрения произвольных данных в диалог произвольного пользователя
1. Внедряем рандомную 32 байтную константу в диалог пользователя из attack_data.
2. Восстанавливаем диалог с этим пользователем использую нашу константу

### IDOR и предсказуемый ID для оплаченных счетов
1. Рассчитываем возможные ID чека для пользователя из attack_data
2. Обращаемся к возможным ID-шникам и получаем флаг

## Как фиксить

### Возможность внедрения произвольных данных в диалог произвольного пользователя
Добавить проверку при добавлении данных в диалог, что имя пользователя соотвествуют авторизованному пользователю.

### IDOR и предсказуемый ID для оплаченных счетов
Изменить генерацию ID для оплаченных чеков.
Добавить проверку при доступе к оплаченному чеку (пользователь является владельцем чека).


## Сплоит
Ищите в репозитории, в папке `/sploits/veladora`.